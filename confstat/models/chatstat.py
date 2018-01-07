# -*- coding: utf-8 -*-
__author__ = 'CubexX'

from datetime import datetime, timedelta

from Crypto.Hash import MD5
from sqlalchemy import BigInteger, Column, Integer, Text

from config import CONFIG
from confstat import cache
from confstat.models import Base
from main import make_db_session


class ChatStat(Base):
    __tablename__ = 'chat_stats'

    id = Column('id', Integer, primary_key=True)
    cid = Column('cid', BigInteger)
    users_count = Column('users_count', Integer, default=0)
    msg_count = Column('msg_count', Integer, default=0)
    last_time = Column('last_time', Integer)
    chat_hash = Column('hash', Text)

    def __init__(self, id=None, cid=None, users_count=None, msg_count=None, last_time=None, chat_hash=None):
        self.id = id
        self.cid = cid
        self.users_count = users_count
        self.msg_count = msg_count
        self.last_time = last_time
        self.chat_hash = chat_hash

    def __repr__(self):
        return "<ChatStat('{}', '{}')>".format(self.cid, self.msg_count)

    @make_db_session
    def add(self, cid, users_count, msg_count, last_time, db):
        chat_stat = self.get(cid)
        today = datetime.today().day

        if chat_stat:
            last_day = datetime.fromtimestamp(chat_stat.last_time).day

            c = ChatStat(cid=cid, msg_count=int(chat_stat.msg_count) + msg_count,
                         users_count=int(chat_stat.users_count) + users_count,
                         last_time=last_time,
                         chat_hash=self.generate_hash(cid))

            if (timedelta(today).days - timedelta(last_day).days) != 0:
                c = ChatStat(cid=cid, msg_count=int(chat_stat.msg_count) + msg_count,
                             users_count=0,
                             last_time=last_time,
                             chat_hash=self.generate_hash(cid))
                db.add(c)
            else:
                self.update(cid, {'msg_count': int(chat_stat.msg_count) + msg_count,
                                  'users_count': int(chat_stat.users_count) + users_count,
                                  'last_time': last_time})
        else:
            c = ChatStat(cid=cid,
                         msg_count=msg_count,
                         users_count=users_count,
                         last_time=last_time,
                         chat_hash=self.generate_hash(cid))
            db.add(c)

        cache.set('cstat_{}'.format(cid), c)
        db.commit()

    @staticmethod
    @make_db_session
    def get(cid, db):
        cached = cache.get('cstat_{}'.format(cid))

        if cached:
            return cached
        else:
            q = db.query(ChatStat) \
                .filter(ChatStat.cid == cid) \
                .order_by(ChatStat.id.desc()) \
                .limit(1) \
                .all()
            if q:
                cache.set('cstat_{}'.format(cid), q[0])
                return q[0]
            else:
                return False

    @staticmethod
    @make_db_session
    def update(cid, update, db):
        update['chat_hash'] = ChatStat.generate_hash(cid)

        sq = db.query(ChatStat.id) \
            .filter(ChatStat.cid == cid) \
            .order_by(ChatStat.id.desc()).limit(1).all()

        db.query(ChatStat) \
            .filter(ChatStat.id == sq[0][0]) \
            .update(update)
        db.commit()

    @staticmethod
    def generate_hash(cid):
        salt = str(CONFIG['salt']).encode('utf-8')
        cid = str(cid).encode('utf-8')

        h = MD5.new(cid)
        h.update(salt)
        chat_hash = h.hexdigest()

        return chat_hash