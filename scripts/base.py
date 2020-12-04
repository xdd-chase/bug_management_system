import django
import os
import sys

# 找到当前脚本的路径，然后加到path中
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bug_management_system.settings')
django.setup()  # 会去读取environ中的配置项DJANGO_SETTINGS_MODEL
