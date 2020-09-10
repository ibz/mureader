import base64
from datetime import datetime
import os
import os.path
from urllib.parse import urlparse

from babel.dates import format_timedelta
import onetimepass

from musocial.main import app, db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    username = db.Column(db.String(255), unique=True)
    public_profile = db.Column(db.Boolean, nullable=False, default=False)
    otp_secret = db.Column(db.String(16))
    password = db.Column(db.String(255))
    registered_on = db.Column(db.DateTime, nullable=False)
    is_pro = db.Column(db.Boolean, nullable=False, default=False)

    subscriptions = db.relationship('Subscription')

    def __init__(self, email):
        self.email = email
        self.otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')
        self.registered_on = datetime.now()

    @property
    def display_name(self):
        return self.username or self.email

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password, app.config.get('BCRYPT_LOG_ROUNDS')).decode()

    def get_totp_uri(self):
        return 'otpauth://totp/musocial:{0}?secret={1}&issuer=musocial'.format(self.email, self.otp_secret)

    def verify_totp(self, token):
        return onetimepass.valid_totp(token, self.otp_secret)

    def verify_password(self, password):
        if not self.password:
            return False
        return bcrypt.check_password_hash(self.password, password)

class Feed(db.Model):
    __tablename__ = 'feeds'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    homepage_url = db.Column(db.String(1000), nullable=False)
    title = db.Column(db.String(1000), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    fetched_at = db.Column(db.DateTime, nullable=True)

    entries = db.relationship('Entry')

    def update(self, parsed_feed):
        self.title = parsed_feed['title']
        self.updated_at = parsed_feed['updated_at']
        self.fetched_at = datetime.now()

        if not self.homepage_url:
            self.homepage_url = parsed_feed.get('homepage_url')
        if not self.homepage_url:
            entry_urls = [e['url'] for e in parsed_feed['entries'] if e['url'].startswith(self.url)]
            self.homepage_url = os.path.commonprefix(entry_urls)

    def update_entries(self, parsed_feed):
        new_entry_urls = set()
        new_entries = []
        updated_entries = []
        for e in parsed_feed['entries']:
            entry = Entry.query.filter_by(url=e['url']).first()
            if not entry:
                if e['url'] not in new_entry_urls:
                    entry = Entry(feed_id=self.id, url=e['url'], title=e['title'],
                        content_from_feed=e['content'],
                        updated_at=e['updated_at'])
                    new_entries.append(entry)
                    new_entry_urls.add(e['url'])
            elif entry.title != e['title'] or entry.updated_at != e['updated_at']:
                entry.title = e['title']
                entry.content_from_feed = e['content']
                entry.updated_at = e['updated_at']
                updated_entries.append(entry)
        return new_entries, updated_entries

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    user = db.relationship(User)
    feed_id = db.Column(db.Integer, db.ForeignKey(Feed.id), primary_key=True)
    feed = db.relationship(Feed)

class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feed_id = db.Column(db.Integer, db.ForeignKey(Feed.id))
    url = db.Column(db.String(1000), unique=True, nullable=False)
    title = db.Column(db.String(1000))
    content_from_feed = db.Column(db.String(10000))
    updated_at = db.Column(db.DateTime)

    @property
    def domain_name(self):
        return urlparse(self.url).netloc

    @property
    def relative_date(self):
        return format_timedelta(self.updated_at - datetime.now(), add_direction=True)

class UserEntry(db.Model):
    __tablename__ = 'user_entries'

    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    user = db.relationship(User)
    entry_id = db.Column(db.Integer, db.ForeignKey(Entry.id), primary_key=True)
    entry = db.relationship(Entry)
    liked = db.Column(db.Boolean, nullable=False, default=False)
