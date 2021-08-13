import base
from web import models


def run():
    models.PricePolicy.objects.create(
        category=2,
        title='VIP',
        price=100,
        project_num=50,
        project_member=10,
        project_space=10,
        per_file_size=100,
    ),
    models.PricePolicy.objects.create(
        category=2,
        title='SVIP',
        price=200,
        project_num=150,
        project_member=50,
        project_space=50,
        per_file_size=500,
    ),
    models.PricePolicy.objects.create(
        category=2,
        title='SSVIP',
        price=500,
        project_num=500,
        project_member=100,
        project_space=100,
        per_file_size=2048,
    )


if __name__ == '__main__':
    run()
