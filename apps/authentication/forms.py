# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

#------------- Home Models -------------#
# Main table
from apps.home.models import Project, Contract, ProjectTimeline
# Foreign table
from apps.home.models import Category, SubCategory, Municipality, Year, Office, FundSource, Remark


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control form-control-lg"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control form-control-lg"
            }
        ))

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control form-control-lg"
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control form-control-lg"
            }
        ))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password check",
                "class": "form-control"
            }
        ))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }

class PasswordUpdateForm(forms.Form):
    """Form for updating user password (basic validation only)."""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "New Password"}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm New Password"}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise ValidationError("New password and confirm password do not match.")

        # You can include further validation of the password here if needed
        return cleaned_data

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter Password"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "is_staff", "is_superuser"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

class UserRoleForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={"class": "form-control select2", 'data-placeholder': 'Select User'})
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        widget=forms.Select(attrs={"class": "form-control select2", 'data-placeholder': 'Select Role'})
    )

# ============================= Form Table =============================================
class UpdateForm(forms.ModelForm):

    search_project_number = forms.ModelChoiceField(
        queryset=Project.objects.values_list('project_number', flat=True).distinct(),
        widget=forms.Select(attrs={"class": "form-control select2", 'data-placeholder': 'Select Number'}), 
        required=False 
    )

    search_project_name = forms.ModelChoiceField(
        queryset=Project.objects.values_list('project_name', flat=True).distinct(),
        widget=forms.Select(attrs={"class": "form-control select2", 'data-placeholder': 'Select Title'}), 
        required=False 
    )

    class Meta:
        model = Project
        fields = '__all__' 
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project name'}),
            'project_ID': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project ID'}),
            'project_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter project description'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'municipality': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select municipality'}),
            'category': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select category'}),
            'sub_category': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select sub_category'}),
            'fund': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select Soucre of Fund'}),
            'office': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select office'}),
            'year': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select year'}),

        }

    def clean(self):
        cleaned_data = super().clean()

        for field, value in cleaned_data.items():
            if value == '':
                cleaned_data[field] = None

        return cleaned_data
    
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__' 
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project name'}),
            'project_ID': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project ID'}),
            'project_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter project description'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'municipality': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select municipality'}),
            'category': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select category'}),
            'sub_category': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select sub_category'}),
            'fund': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select Soucre of Fund'}),
            'office': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select office'}),
            'year': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select year'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        for field in self.fields:  # Iterate over form fields
            if cleaned_data.get(field) == '':
                cleaned_data[field] = None  # Convert empty string to None

        return cleaned_data

class ProjectTimelineForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ProjectTimeline
        fields = '__all__'
        widgets = {
            'cd': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter CD'}),
            'ntp_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'extension': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter number of extension'}),
            'target_completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'revised_completion_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Revised Date'}),
            'date_completed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_cost_incurred_to_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Incurred Date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Reason'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that all number fields are non-negative
        number_fields = ['cd', 'extension']
        for field in number_fields:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, "This field cannot be negative.")

        for field, value in cleaned_data.items():
            if value == '':
                cleaned_data[field] = None

        return cleaned_data

class ContractForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Contract
        fields = '__all__'
        widgets = {
            'project_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter Project cost'}),
            'contract_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter Contract cost'}),
            'quarter' : forms.NumberInput(attrs={'class': 'form-control', 'min': '0.0001', 'max': '1', 'step': '0.0001', 'placeholder': 'Enter quarter'}),
            'procurement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Procurement'}),
            'project_contractor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Contractor'}),
            'tin_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Tin number'}),
            'remarks': forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Select remarks'}),
        }
    
    def clean_quarter(self):
        quarter = self.cleaned_data.get('quarter')
        if quarter is not None and (quarter < 0.0001 or quarter > 1):
            raise ValidationError("Quarter must be between 0.0001 and 1.")
        return quarter

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that all number fields are non-negative
        number_fields = ['project_cost', 'contract_cost']
        for field in number_fields:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, "This field cannot be negative.")

        for field, value in cleaned_data.items():
            if value == '':
                cleaned_data[field] = None

        return cleaned_data

class FundSourceForm(forms.ModelForm):
    class Meta:
            model = FundSource
            fields = '__all__' 
            widgets = {
                'fund': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter New Fund'})
            }

class CategoryForm(forms.ModelForm):
    class Meta:
            model = Category
            fields = '__all__' 
            widgets = {
                'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter New Category'})
            }

class SubCategoryForm(forms.ModelForm):
    class Meta:
            model = SubCategory
            fields = '__all__' 
            widgets = {
                'sub_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter New Sub Category'})
            }

class OfficeForm(forms.ModelForm):
    class Meta:
            model = Office
            fields = '__all__' 
            widgets = {
                'office': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter New office'})
            }

class YearForm(forms.ModelForm):
    class Meta:
        model = Year
        fields = '__all__'
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Enter New Year'})
        }

    # Custom validation to ensure the year is a positive number
    def clean_year(self):
        year = self.cleaned_data.get('year')
        
        if year <= 0:
            raise forms.ValidationError("Year must be a positive integer.")
        
        # Optionally, you can also check for reasonable year ranges, e.g. no future years
        if year > 9999:
            raise forms.ValidationError("Year must be a valid year (4 digits).")
        
        return year

# ============================= Dump table Storage =============================================
class UploadFileForm(forms.Form):
    file = forms.FileField()

