from django.contrib import admin
from .models import Image, Property,Feedback,Wishlist,LoanApplicant,Nominee,HomeInteriors,CompareProperty

# Register your models here.
admin.site.register(Property)
admin.site.register(Image)
admin.site.register(Feedback)
admin.site.register(Wishlist)
admin.site.register(LoanApplicant)
admin.site.register(Nominee)
admin.site.register(HomeInteriors)
admin.site.register(CompareProperty)