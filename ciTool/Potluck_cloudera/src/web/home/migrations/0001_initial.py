# encoding: utf8
from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Solution',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Build',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('solution', models.ForeignKey(to='home.Solution', to_field=u'id')),
                ('version', models.CharField(max_length=512)),
                ('platform_version', models.CharField(max_length=512)),
                ('image_path', models.CharField(help_text='Full Image URL e.g. http://192.168.0.17/release/appanalytics/2.0/2.0.d1/appanalytics2.0.d1/image-appanalytics2.0.d1.img', max_length=2048)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestsuiteExecution',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('build', models.ForeignKey(to='home.Build', to_field=u'id')),
                ('suite', models.CharField(max_length=512)),
                ('testbed', models.CharField(max_length=512)),
                ('ui_url', models.CharField(max_length=512, null=True, verbose_name='Url of the UI', blank=True)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True)),
                ('completed_at', models.DateTimeField(null=True, blank=True)),
                ('state', models.IntegerField(default=1, choices=[(1, 'Enqueued'), (2, 'Running'), (3, 'Completed'), (4, 'LIMBO')])),
                ('status', models.IntegerField(blank=True, null=True, choices=[(1, 'Passed'), (2, 'Failed')])),
                ('logs_path', models.TextField()),
                ('harness_output', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestcaseExecution',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('suite_execution', models.ForeignKey(to='home.TestsuiteExecution', to_field=u'id')),
                ('tc_id', models.CharField(max_length=256)),
                ('script', models.CharField(max_length=512)),
                ('section', models.CharField(max_length=512)),
                ('started_at', models.DateTimeField(null=True, blank=True)),
                ('completed_at', models.DateTimeField(null=True, blank=True)),
                ('logs_path', models.TextField()),
                ('state', models.IntegerField(default=1, choices=[(1, 'Not Run'), (2, 'Running'), (3, 'Completed'), (4, 'LIMBO')])),
                ('status', models.IntegerField(default=3, choices=[(1, 'Passed'), (2, 'Failed'), (3, 'Not Run')])),
                ('remarks', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
