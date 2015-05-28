import plugintypes
from DatabaseMixin import DatabaseMixin, DbType
import tgl
import time
from datetime import datetime
import parsedatetime.parsedatetime as pdt
import threading


class RemindMePlugin(plugintypes.TelegramPlugin, DatabaseMixin):
    """
    Register a reminder with the bot
    """
    patterns = {
        "^!(remindme|reminder|remind) (.*)": "set_reminder",
    }

    usage = [
        "!remindme <time specifier> <message>: Set message reminder",
    ]

    schema = {
        'timestamp': DbType.DateTime,
        'remindtime': DbType.DateTime,
        'chat_id': DbType.Integer,
        'chat_type': DbType.Integer,
        'msg_id': DbType.Integer,
        'msg': DbType.String
    }

    def __init__(self):
        super().__init__()
        DatabaseMixin.__init__(self)
        # Prime reminder check.
        self.check_reminder()

    def set_reminder(self, msg, matches):
        message = matches.group(2)
        date = msg.date
        remind_date = pdt.Calendar().parse(message)
        remind_date = time.strftime('%Y-%m-%d %H:%M:%S', remind_date[0])

        self.insert(timestamp=msg.date,
                    remindtime=remind_date,
                    chat_id=self.bot.get_peer_to_send(msg).id,
                    chat_type=self.bot.get_peer_to_send(msg).type,
                    msg_id=msg.id,
                    msg=msg.text
        )

        return "Will remind @{} at {}".format(msg.src.username, remind_date)


    def check_reminder(self):
        # Call again in 30 seconds
        threading.Timer(30.0, self.check_reminder).start()
        results = self.query("SELECT * FROM {0} WHERE remindtime < DATETIME('now','localtime')".format(self.table_name))
        for result in results:
            try:
                peer = tgl.Peer(id=result['chat_id'], type=result['chat_type'])
                peer.send_msg("Remember!", reply=result['msg_id'])
                self.query("DELETE FROM {0} WHERE msg_id = {1}".format(self.table_name, result['msg_id']))
            except SystemError:
                # Don't have the peer in the peer_tree yet in tg, try again in a minute, bot was probably recently
                # launched.
                pass
