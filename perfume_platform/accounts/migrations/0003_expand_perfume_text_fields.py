from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_schema_defaults')]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE perfume "
                "MODIFY COLUMN concentration VARCHAR(50) NOT NULL, "
                "MODIFY COLUMN recommended_season VARCHAR(100) NULL"
            ),
            reverse_sql=(
                "ALTER TABLE perfume "
                "MODIFY COLUMN concentration ENUM(\'EDT\',\'EDP\',\'Parfum\',\'EDC\',\'Cologne\') NOT NULL, "
                "MODIFY COLUMN recommended_season ENUM(\'Spring\',\'Summer\',\'Fall\',\'Winter\',\'All Season\') NULL"
            ),
        ),
    ]
