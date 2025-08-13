from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure_database', '0005_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='transactions', to='infrastructure_database.client'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['client'], name='tx_client_idx'),
        ),
    ]


