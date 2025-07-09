from django.contrib import admin
from category.models import Category, Product, ProductImage, ProductSize

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_main']
    readonly_fields = []

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'stock']


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ['category_name', 'slug', 'created_at']
    search_fields = ('category_name',)


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('product_name',)}
    list_display = ('product_name', 'vendor', 'price', 'is_available', 'updated_at')
    search_fields = ('product_name', 'categories__category_name', 'vendor__vendor_name', 'price')
    list_filter = ('is_available', 'is_featured', 'is_new', 'categories')
    inlines = [ProductImageInline, ProductSizeInline]

    filter_horizontal = ('categories',)  # pour bien afficher le champ ManyToMany
    autocomplete_fields = ['vendor']     # si tu as beaucoup de vendeurs

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
