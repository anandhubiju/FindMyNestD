from django import forms
from .models import User


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )

class CustomUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id':'pass',
        "class": "form-control form-control-lg",
        'placeholder': 'Enter Password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'id':'cpass',
        "class": "form-control form-control-lg",
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = User
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                "class": "form-control form-control-lg ",
                'placeholder': 'Enter Name',
                'id':'name'
            }),
            'email': forms.EmailInput(attrs={
                'id':'email',
                "class": "form-control form-control-lg",
                'placeholder': 'Enter Email'
            }),
            'phone': forms.TextInput(attrs={
                'id':'phone',
                "class": "form-control form-control-lg",
                'placeholder': 'Enter Phone Number'
            }),
            # 'role': forms.Select(attrs={
            #     "class": "form-control form-control-lg"
            # }),

        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password)
        
        if commit:
            user.save()
        return user