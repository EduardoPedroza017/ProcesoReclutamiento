"""
Serializers para la app de Clients
"""
from rest_framework import serializers
from .models import Client, ContactPerson


class ContactPersonSerializer(serializers.ModelSerializer):
    """Serializer para ContactPerson"""
    
    class Meta:
        model = ContactPerson
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer para Client"""
    
    contacts = ContactPersonSerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    full_address = serializers.CharField(read_only=True)
    active_profiles_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear clientes"""
    
    contacts = ContactPersonSerializer(many=True, required=False)
    
    class Meta:
        model = Client
        exclude = ['created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', [])
        client = Client.objects.create(**validated_data)
        
        for contact_data in contacts_data:
            ContactPerson.objects.create(client=client, **contact_data)
        
        return client