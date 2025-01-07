from django.contrib import admin

from .models import Post, Category, Location, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'is_published',
        'author',
        'category',
        'location'
    )
    list_editable = (
        'pub_date',
        'is_published',
        'category'
    )

    search_fields = ('title',)
    list_filter = ('category',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'is_published',
        'slug',
    )
    list_editable = (
        'is_published',
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location)
admin.site.register(Comment)
