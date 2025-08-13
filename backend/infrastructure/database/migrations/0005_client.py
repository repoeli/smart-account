from django.db import migrations, models
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure_database', '0004_transaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('company_name', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='clients', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'clients',
                'ordering': ['name', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['owner'], name='clients_owner_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['name'], name='clients_name_idx'),
        ),
    ]


