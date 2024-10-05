from snippets.lab3 import Server
from snippets.lab4.users import UserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class RPCServer(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = UserDatabase()
    
    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'connect':
                connection.callback = self.__on_message_event
    
    def __on_message_event(self, event, payload, connection, error):
        match event:
            case 'message':
                request = deserialize(payload)
                assert isinstance(request, Request)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                connection.close()
    
    def __handle_request(self, request):
        try:
            method = getattr(self.__user_db, request.name)
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = str(e)
        return Response(result, error)



    