# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsuiteexecution',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, to_field=u'id'),
            preserve_default=False,
        ),
    ]
