# Generated by Django 2.2.9 on 2021-05-25 09:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("posts", "0002_auto_20210525_1244")]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="posts",
                to="posts.Group",
            ),
        )
    ]