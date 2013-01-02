import uuid

from groundstation.proto.gizmo_pb2 import Gizmo
from groundstation.proto import request_pb2

from groundstation import logger
log = logger.getLogger(__name__)

class InvalidRequest(Exception):
    pass

class Request(object):
    __Response = None
    def __init__(self, verb, station=None, stream=None, payload=None, origin=None):
        # Cheat and load this at class definition time
        if not self.__Response:
            res = __import__("groundstation.transfer.response")
            self.__Response = res.transfer.response.Response
        self.type = "REQUEST"
        self.id = uuid.uuid1()
        self.verb = verb
        self.station = station
        self.stream = stream
        self.payload = payload
        # if origin:
        #     self.origin = uuid.UUID(origin)
        self.origin = origin
        self.validate()

    def _Response(self, *args, **kwargs):
        kwargs['station'] = self.station
        return self.__Response(*args, **kwargs)


    @classmethod
    def from_gizmo(klass, gizmo, station, stream):
        log.debug("Hydrating a request from gizmo: %s" % (str(gizmo)))
        return klass(gizmo.verb, station, stream, gizmo.payload, gizmo.stationid)

    def SerializeToString(self):
        gizmo = self.station.gizmo_factory.gizmo()
        g_request = request_pb2.Request()

        gizmo.id = str(self.id)
        gizmo.type = Gizmo.REQUEST

        g_request.verb = self.verb

        if self.payload:
            g_request.payload = self.payload

        gizmo.payload = g_request.SerializeToString()
        return gizmo.SerializeToString()

    def validate(self):
        if self.verb not in self.VALID_REQUESTS:
            raise Exception("Invalid Request: %s" % (self.verb))

    def process(self):
        self.VALID_REQUESTS[self.verb](self)

    def handle_listallobjects(self):
        if not self.station.recently_queried(self.origin):
            log.info("%s not up to date, issuing LISTALLOBJECTS" % (self.origin))
            listobjects = Request("LISTALLOBJECTS", station=self.station)
            self.stream.enqueue(listobjects)
        else:
            log.info("object cache for %s still valid" % (self.origin))
        log.info("Handling LISTALLOBJECTS")
        payload = self.station.objects()
        log.info("Sending %i object descriptions" % (len(payload)))
        response = self._Response(self.id, "DESCRIBEOBJECTS",
                                chr(0).join(payload))
        self.stream.enqueue(response)
        self.TERMINATE()

    def handle_fetchobject(self):
        log.info("Handling FETCHOBJECT for %s" % (repr(self.payload)))
        response = self._Response(self.id, "TRANSFER", self.station.repo[self.payload])
        self.stream.enqueue(response)

    def TERMINATE(self):
        terminate = self._Response(self.id, "TERMINATE", None)
        self.stream.enqueue(terminate)

    VALID_REQUESTS = {
            "LISTALLOBJECTS": handle_listallobjects,
            "FETCHOBJECT": handle_fetchobject,
    }
