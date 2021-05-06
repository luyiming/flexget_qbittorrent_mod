import copy

from PIL import Image
from flexget import plugin
from flexget.components.notify.notifiers.telegram import TelegramNotifier
from flexget.event import event
from flexget.manager import Session
from flexget.plugin import PluginWarning

try:
    import telegram
    from telegram.error import TelegramError
    from telegram.utils.request import NetworkError
except ImportError:
    telegram = None
    TelegramError = None

_IMAGE_ATTR = 'image'
_TEXT_LIMIT = 4096
_PLUGIN_NAME = 'telegram_mod'


def dict_merge(dict1, dict2):
    for i in dict2:
        if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
            dict_merge(dict1[i], dict2[i])
        else:
            dict1[i] = dict2[i]


class TelegramNotifierMod(TelegramNotifier):
    schema = copy.deepcopy(TelegramNotifier.schema)
    dict_merge(schema, {
        'properties': {
            _IMAGE_ATTR: {'type': 'string'}
        }
    })

    def notify(self, title, message, config):
        """
        Send a Telegram notification
        """
        chat_ids = self._real_init(Session(), config)

        if not chat_ids:
            return
        msg_limits = self._get_msg_limits(message)
        for msg_limit in msg_limits:
            self._send_msgs(msg_limit, chat_ids)
        if self._image:
            self._send_photo(self._image, chat_ids)

    def _parse_config(self, config):
        super(TelegramNotifierMod, self)._parse_config(config)
        self._image = config.get(_IMAGE_ATTR)

    def _get_msg_limits(self, msg):
        msg_limits = ['']
        if len(msg) < _TEXT_LIMIT:
            return [msg]
        msg_lines = msg.split('\n')
        for line in msg_lines:
            if len(msg_limits[-1] + line) > _TEXT_LIMIT and len(msg_limits[-1]) > 0:
                msg_limits.append('')
            msg_limits[-1] = msg_limits[-1] + line

    def _send_photo(self, image, chat_ids):
        for chat_id in (x.id for x in chat_ids):
            try:
                photo = Image.open(image)
                width = photo.width
                height = photo.height
                if width + height > 10000 or width / height > 20:
                    self._bot.sendDocument(chat_id=chat_id, document=open(image, 'rb'))
                else:
                    self._bot.sendPhoto(chat_id=chat_id, photo=open(image, 'rb'))
            except TelegramError as e:
                raise PluginWarning(e.message)


@event('plugin.register')
def register_plugin():
    plugin.register(TelegramNotifierMod, _PLUGIN_NAME, api_ver=2, interfaces=['notifiers'])
