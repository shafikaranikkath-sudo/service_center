from django.shortcuts import render,get_object_or_404

# Create your views here.
## 🛂 Role helpers (in attendance/views.py top)
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group

from .forms import UserUpdateForm,ProfileUpdateForm,ProfilePicForm

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import CheckLog
from .forms import UserCreateForm

def in_group(name):
    def check(user):
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name=name).exists())
        return user_passes_test(check)


is_admin = in_group('Admin')
is_manager = in_group('Manager')
is_staff_role = in_group('Staff')



## 🖥 attendance/views.py



# ---- Auth ----
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('attendance:dashboard')
        messages.error(request, 'Invalid credentials')
    return render(request, 'attendance/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('attendance:login')


# ---- Dashboard ----
@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():
        total_users = User.objects.count()
        open_logs = CheckLog.objects.filter(check_out_time__isnull=True).select_related('user')
        today_logs = CheckLog.objects.filter(check_in_time__date=timezone.localdate())
        ctx = {'total_users': total_users, 'open_logs': open_logs, 'today_logs': today_logs}
        return render(request, 'attendance/dashboard_admin.html', ctx)
    

    if request.user.groups.filter(name='Manager').exists():
        # For simplicity, managers can view everyone; extend to teams later
        logs = CheckLog.objects.filter(check_in_time__date=timezone.localdate()).select_related('user')
        return render(request, 'attendance/dashboard_manager.html', {'logs': logs})
    # Staff
    last_log = CheckLog.objects.filter(user=request.user).first()
    has_open = CheckLog.objects.filter(user=request.user, check_out_time__isnull=True).exists()
    return render(request, 'attendance/dashboard_staff.html', {'last_log': last_log, 'has_open': has_open})

# ---- Check In / Out ----
@login_required
def check_in(request):
    if CheckLog.objects.filter(user=request.user, check_out_time__isnull=True).exists():
        messages.warning(request, 'You already have an open shift. Please check out first.')
        return redirect('attendance:dashboard')
    CheckLog.objects.create(user=request.user)
    messages.success(request, 'Checked in successfully!')
    return redirect('attendance:dashboard')

@login_required
def check_out(request):
    log = CheckLog.objects.filter(user=request.user, check_out_time__isnull=True).first()
    if not log:
        messages.warning(request, 'No open shift to check out from.')
        return redirect('attendance:dashboard')
    log.check_out_time = timezone.now()
    log.save()
    messages.success(request, 'Checked out successfully!')
    return redirect('attendance:dashboard')

# ---- Logs & Reports ----
@login_required
def logs_list(request):
    # Admin/Manager see all; Staff see own
    if request.user.groups.filter(name__in=['Admin','Manager']).exists() or request.user.is_superuser:
        logs = CheckLog.objects.select_related('user').all()
    else:
        logs = CheckLog.objects.filter(user=request.user)
    q_user = request.GET.get('user')
    q_date = request.GET.get('date') # YYYY-MM-DD
    if q_user:
        logs = logs.filter(user__username__icontains=q_user)
    if q_date:
        logs = logs.filter(check_in_time__date=q_date)
    return render(request, 'attendance/logs_list.html', {'logs': logs})

# ---- User management (Admin only) ----
@login_required
def users_list(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Admin','Manager']).exists()):
        return HttpResponseForbidden('Admins/Managers only')
    role_filter = request.GET.get("role")

    users = User.objects.exclude(is_superuser=True)

    if role_filter:
        users = users.filter(groups__name=role_filter)
    roles = ['Admin', 'Manager', 'Staff']  # available roles

    return render(request, 'attendance/user_list.html', {"users": users,"roles": roles,"selected_role": role_filter,})

@login_required
def user_create(request):
    if not (request.user.is_superuser or request.user.groups.filter(name='Admin').exists()):
        return HttpResponseForbidden('Admins only')

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                role = form.cleaned_data['role']
                group, _ = Group.objects.get_or_create(name=role)
                user.groups.add(group)
                messages.success(request, f'User {user.username} created as {role}.')
                return redirect('attendance:users_list')
    else:
        # ⚡ Define form for GET requests
        form = UserCreateForm()

    return render(request, 'attendance/user_create.html', {'form': form})


@login_required
def user_edit(request, user_id):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Admin','Manager']).exists()):
        return HttpResponseForbidden("Admins/Managers only")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully")
            return redirect("attendance:users_list")
    else:
        form = UserUpdateForm(instance=user)

    return render(request, "attendance/user_edit.html", {"form": form, "user_obj": user})            

@login_required
def user_delete(request, user_id):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Admin','Manager']).exists()):
        return HttpResponseForbidden("Admins/Managers only")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully")
        return redirect("attendance:users_list")

    return render(request, "attendance/user_confirm_delete.html", {"user_obj": user})

@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep user logged in
            messages.success(request, "Your password was changed successfully")
            return redirect("attendance:dashboard")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "attendance/change_password.html", {"form": form})

@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        pic_form = ProfilePicForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid() and pic_form.is_valid():
            form.save()
            pic_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("attendance:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)
        pic_form = ProfilePicForm(instance=request.user.profile)

    return render(request, "attendance/profile.html", {
        "form": form,
        "pic_form": pic_form,
    })