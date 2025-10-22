from django.contrib import admin
from .models import User, Course, Chapter, Exercise, Subscription, Transaction, UserSubscription

# Register your models here.

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'duration']
    list_editable = ['is_active']
    ordering = ['price']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Pricing Details', {
            'fields': ('price', 'duration')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subscription', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'user__username', 'stripe_payment_intent_id', 'description']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_customer_id', 'created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User & Subscription', {
            'fields': ('user', 'subscription')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_customer_id')
        }),
        ('Transaction Details', {
            'fields': ('amount', 'currency', 'status', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual creation of transactions
        return False


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subscription', 'start_date', 'end_date', 'is_active', 'auto_renew']
    list_filter = ['is_active', 'auto_renew', 'start_date', 'end_date']
    search_fields = ['user__email', 'user__username', 'subscription__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('User & Subscription', {
            'fields': ('user', 'subscription', 'transaction')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date', 'is_active', 'auto_renew')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ['is_active']
