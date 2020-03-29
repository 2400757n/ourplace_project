# Generated by Django 2.2.3 on 2020-03-29 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ourplace', '0002_canvas_bitmap'),
    ]

    operations = [
        migrations.AddField(
            model_name='canvas',
            name='owner',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='ourplace.UserProfile'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='canvasaccess',
            name='canvas',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='ourplace.Canvas'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='canvasaccess',
            name='user',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='ourplace.UserProfile'),
            preserve_default=False,
        ),
    ]
