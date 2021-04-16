from PyQt5.QtCore import QUrl, QUrlQuery, QDateTime
from qgis.PyQt.QtCore import pyqtSignal, QObject, Qt
from PyQt5 import QtNetwork
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
import json

THERMAL_ANOMALY_URL = "http://172.26.200.45/lib/get_taPlugin.php"


class DataRequest(QObject):

    requestFinished = pyqtSignal([list, str])

    def __init__(self):
        super().__init__()
        self.__manager = QtNetwork.QNetworkAccessManager()

    def dataRequest(self, statuses, satellites, belarus, date_from, date_to, polygon):

        date_format = "dd.MM.yyyy hh:mm"
        url = QUrl(THERMAL_ANOMALY_URL)
        url_query = QUrlQuery()
        if polygon is not None:
            url_query.addQueryItem("polygon", polygon)
        if date_from is not None:
            url_query.addQueryItem("date_from", date_from.toString(date_format))
        if date_to is not None:
            url_query.addQueryItem("date_to", date_to.toString(date_format))
        url_query.addQueryItem("only_rb", str(belarus))
        url_query.addQueryItem("type", "array")
        if len(statuses) > 0:
            url_query.addQueryItem("state", ','.join(map(str, statuses)))
        if len(satellites) > 0:
            url_query.addQueryItem("tts", ','.join(map(str, satellites)))
        url.setQuery(url_query)

        print(url_query.queryItems())

        request = QtNetwork.QNetworkRequest()
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json".encode())
        request.setUrl(url)
        # print("request: ", url)

        self.data_reply = self.__manager.post(request, url_query.toString(QUrl.FullyEncoded).encode())
        self.data_reply.finished.connect(lambda dr=self.data_reply: self.__data_request_finished(dr))

    def __data_request_finished(self, data_reply):
        # print("finished with: ", dataReply.url())
        result_items = []
        msg = None

        if data_reply is None or data_reply.error() != QtNetwork.QNetworkReply.NoError:
            if data_reply is not None:
                msg = "data error: " + str(data_reply.error()) + ", " + self.__error_string(data_reply.error())
                print(msg)
                print(str(data_reply.readAll(), 'utf-8'))
                print(data_reply.url())
                headers = data_reply.rawHeaderList()
                for key in headers:
                    print(key, '->', data_reply.rawHeader(key))
        else:
            data = str(data_reply.readAll(), 'utf-8')
            if len(data) > 0:
                try:
                    result_items = json.loads(data)
                    if result_items is None:
                        result_items = []
                except ValueError as e:
                    print(e)
                    msg = "Wrong server response. Can't be converted to json"
                    # print(data)
            else:
                print(type(data))
                print(data_reply.readAll())
                print(data_reply.error())

        self.requestFinished.emit(result_items, msg)

    def print_known_headers(self, reply):
        print("ContentTypeHeader: ", reply.header(QNetworkRequest.ContentTypeHeader))
        print("ContentLengthHeader: ", reply.header(QNetworkRequest.ContentLengthHeader))
        print("LocationHeader: ", reply.header(QNetworkRequest.LocationHeader))
        print("LastModifiedHeader: ", reply.header(QNetworkRequest.LastModifiedHeader))
        print("CookieHeader: ", reply.header(QNetworkRequest.CookieHeader))
        print("SetCookieHeader: ", reply.header(QNetworkRequest.SetCookieHeader))
        print("UserAgentHeader: ", reply.header(QNetworkRequest.UserAgentHeader))
        print("ServerHeader: ", reply.header(QNetworkRequest.ServerHeader))

    def __error_string(self, code):
        if code == QtNetwork.QNetworkReply.NoError:
            return 'no error'
        if code == QNetworkReply.ConnectionRefusedError:
            return 'ConnectionRefusedError'
        if code == QNetworkReply.RemoteHostClosedError:
            return 'RemoteHostClosedError'
        if code == QNetworkReply.HostNotFoundError:
            return 'HostNotFoundError'
        if code == QNetworkReply.TimeoutError:
            return 'TimeoutError'
        if code == QNetworkReply.OperationCanceledError:
            return 'OperationCanceledError'
        if code == QNetworkReply.SslHandshakeFailedError:
            return 'SslHandshakeFailedError'
        if code == QNetworkReply.TemporaryNetworkFailureError:
            return 'TemporaryNetworkFailureError'
        if code == QNetworkReply.NetworkSessionFailedError:
            return 'NetworkSessionFailedError'
        if code == QNetworkReply.BackgroundRequestNotAllowedError:
            return 'BackgroundRequestNotAllowedError'
        if code == QNetworkReply.TooManyRedirectsError:
            return 'TooManyRedirectsError'
        if code == QNetworkReply.InsecureRedirectError:
            return 'InsecureRedirectError'
        if code == QNetworkReply.ProxyConnectionRefusedError:
            return 'ProxyConnectionRefusedError'
        if code == QNetworkReply.ProxyConnectionClosedError:
            return 'ProxyConnectionClosedError'
        if code == QNetworkReply.ProxyNotFoundError:
            return 'ProxyNotFoundError'
        if code == QNetworkReply.ProxyTimeoutError:
            return 'ProxyTimeoutError'
        if code == QNetworkReply.ProxyAuthenticationRequiredError:
            return 'ProxyAuthenticationRequiredError'
        if code == QNetworkReply.ContentAccessDenied:
            return 'ContentAccessDenied'
        if code == QNetworkReply.ContentOperationNotPermittedError:
            return 'ContentOperationNotPermittedError'
        if code == QNetworkReply.ContentNotFoundError:
            return 'ContentNotFoundError'
        if code == QNetworkReply.AuthenticationRequiredError:
            return 'AuthenticationRequiredError'
        if code == QNetworkReply.ContentReSendError:
            return 'ContentReSendError'
        if code == QNetworkReply.ContentConflictError:
            return 'ContentConflictError'
        if code == QNetworkReply.ContentGoneError:
            return 'ContentGoneError'
        if code == QNetworkReply.InternalServerError:
            return 'InternalServerError'
        if code == QNetworkReply.OperationNotImplementedError:
            return 'OperationNotImplementedError'
        if code == QNetworkReply.ServiceUnavailableError:
            return 'ServiceUnavailableError'
        if code == QNetworkReply.ProtocolUnknownError:
            return 'ProtocolUnknownError'
        if code == QNetworkReply.ProtocolInvalidOperationError:
            return 'ProtocolInvalidOperationError'
        if code == QNetworkReply.UnknownNetworkError:
            return 'UnknownNetworkError. An unknown network-related error was detected'
        if code == QNetworkReply.UnknownProxyError:
            return 'UnknownProxyError'
        if code == QNetworkReply.UnknownContentError:
            return 'UnknownContentError'
        if code == QNetworkReply.ProtocolFailure:
            return 'ProtocolFailure. A breakdown in protocol was detected'
        if code == QNetworkReply.UnknownServerError:
            return 'UnknownServerError. An unknown error related to the server response was detected'
        return 'UnknownError. Error with unknown error code'
