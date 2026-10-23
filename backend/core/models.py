from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
import hashlib
import uuid


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'


class Phone(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('stolen', 'Stolen'),
        ('recovered', 'Recovered'),
        ('lost', 'Lost'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    imei = models.CharField(max_length=20, unique=True)
    imei_hash = models.CharField(max_length=64, unique=True)
    model = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_location = gis_models.PointField(null=True, blank=True, srid=4326)
    
    class Meta:
        db_table = 'phones'
        indexes = [
            models.Index(fields=['imei_hash']),
            models.Index(fields=['status']),
        ]


class Detection(models.Model):
    DETECTION_TYPE_CHOICES = [
        ('ble_scan', 'BLE Scan'),
        ('gps_check', 'GPS Check'),
        ('manual_report', 'Manual Report'),
    ]
    
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='detections')
    detector_device_id = models.CharField(max_length=100, blank=True)
    detection_type = models.CharField(max_length=20, choices=DETECTION_TYPE_CHOICES)
    location = gis_models.PointField(srid=4326)
    detected_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(default=0.0)  # 0.0 to 1.0
    is_confirmed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'detections'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['detected_at']),
            models.Index(fields=['is_confirmed']),
        ]


class Report(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('police_filed', 'Police Filed'),
        ('closed', 'Closed'),
    ]
    
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, default='ZRP Statement')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    pdf_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
        ]


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('paynow', 'Paynow'),
        ('ecocash', 'EcoCash'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['reference_id']),
            models.Index(fields=['user']),
        ]


class Notification(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=[('whatsapp', 'WhatsApp'), ('sms', 'SMS'), ('email', 'Email')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(null=True, blank=True)
    twilio_message_sid = models.CharField(max_length=34, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'