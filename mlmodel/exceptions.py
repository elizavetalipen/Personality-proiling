

class NotFoundError(Exception):
    def __init__(self, error_message="This resource was not found, check the url"):
        self.error_message = error_message
        self.status_code = 404
        super().__init__(self.error_message)


class ValidationError(Exception):
    def __init__(self, error_message="Validation error: there were invalid fields in the request"):
        self.error_message = error_message
        self.status_code = 400
        super().__init__(self.error_message)


