from proto.gizmo_pb2 import Gizmo
from google.protobuf.message import DecodeError
from transfer.request import Request
from transfer.response import Response

import groundstation.logger
log = groundstation.logger.getLogger(__name__)

class GizmoFactory(object):
    builders = {
            Gizmo.REQUEST: Request,
            Gizmo.RESPONSE: Response
    }
    def __init__(self, station):
        self.station = station

    def hydrate(self, data, stream):
        gizmo = Gizmo()
        try:
            gizmo.ParseFromString(data)
        except DecodeError:
            raise InvalidGizmoError("Couldn't decode gizmo")
        try:
            self.builders[gizmo.type](gizmo, self.station, stream)
        except KeyError:
            raise Exception("Invalid message type")

class InvalidGizmoError(Exception):
    def __init__(self, msg):
        log.warn(msg)
        super(InvalidGizmoError, self).__init__(self)