source ~/.bash_profile
git pull origin master:master
cd clone_twitter
source /home/ec2-user/venv/bin/activate
pip3 install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py check --deploy
sudo pkill gunicorn
gunicorn twitter.wsgi:application --bind 0.0.0.0:8000 --daemon

sudo systemctl restart nginx
