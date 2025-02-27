import requests, urllib3

urllib3.disable_warnings()  # Suppresses SSL warnings

class SMAXClient:
    
    def __init__(self, base_url, tenant_id, username, password):
        """
        Initialize the SMAX API Client.
        
        :param base_url: SMAX instance URL (e.g., "https://smax.example.com")
        :param tenant_id: SMAX Tenant ID
        :param username: SMAX Username
        :param password: SMAX Password
        """
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.verify = False  # Disable SSL verification
        self.token = None
        self.authenticate()  # Authenticate on initialization

    def authenticate(self):
        """Authenticate and retrieve an access token."""
        url = f"{self.base_url}/auth/authentication-endpoint/authenticate/token?TENANTID={self.tenant_id}"
        payload = {"login": self.username, "password": self.password}

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)

            self.token = response.text.strip()  # SMAX returns token as plain text
            self.session.headers["Cookie"] = f"SMAX_AUTH_TOKEN={self.token}"  # Use token in Cookie header
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error during authentication: {str(e)}")

    @staticmethod
    def handle_error(response, method=None, url=None, params=None, request=None):
        """Handles API response errors with logging and structured error messages."""

        error_messages = {
            400: "Invalid request",
            401: "Unauthorized",
            405: "Method not allowed",
            500: "Internal server error"
        }
        
        log_data = {
            "ERROR": error_messages.get(response.status_code),        
            "HTTP method": method, 
            "HTTP URL": url, 
            "HTTP params": params, 
            "HTTP request": request, 
            "HTTP response": response.text, 
            "HTTP status code": response.status_code
        }
        
        for key, value in log_data.items():
            if value:
                print(f"{key}: {value}")
    
    def make_request(self, method, endpoint, data=None, params=None, retry=True):
        """
        Make a request to the SMAX API.
        """
        url = f"{self.base_url}/rest/{self.tenant_id}{endpoint}"
        
        # Exit if token is null
        if not self.token:
            exit()
        
        try:
            response = self.session.request(method, url, json=data, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()

        except requests.exceptions.HTTPError as e:
        
            if response.status_code == 401:
                if retry:
                    self.authenticate() # re-authenticate
                    return self.make_request(method, endpoint, data, params, retry=False) # try again
                else:
                    print("[ERROR] Failed to re-authenticate.")
            else:
                self.handle_error(response, method=method, url=url, params=params, request=data)
            
        except requests.exceptions.RequestException as e:
            return {"[ERROR] ": str(e)}
    
    @staticmethod
    def _filter_params(**kwargs):
        """Helper function to filter out None values from parameters."""
        return {k: v for k, v in kwargs.items() if v is not None}

    def query_entities(self, entity_type, filter=None, layout=None, group=None, order=None, size=None, skip=None, meta=None):
        """Query entities with optional filters."""
        params = self._filter_params(layout=layout, filter=filter, group=group, order=order, size=size, skip=skip, meta=meta)
        return self.make_request("GET", f"/ems/{entity_type}", params=params)

    def get_entity(self, entity_type, entity_id, layout):
        """Retrieve a single entity by ID."""
        return self.make_request("GET", f"/ems/{entity_type}/{entity_id}", params={"layout": layout})

    def get_related_records(self, entity_type, entity_id, association, layout, filter=None, group=None, order=None, size=None, skip=None, meta=None):
        """Retrieve related records based on an association."""
        params = self._filter_params(layout=layout, filter=filter, group=group, order=order, size=size, skip=skip, meta=meta)
        return self.make_request("GET", f"/ems/{entity_type}/{entity_id}/associations/{association}", params=params)

    def get_aggregated_data(self, entity_type, layout, filter=None, group=None, order=None, size=None, skip=None, meta=None):
        """Retrieve aggregated data."""
        params = self._filter_params(layout=layout, filter=filter, group=group, order=order, size=size, skip=skip, meta=meta)
        return self.make_request("GET", f"/ems/{entity_type}/aggregations", params=params)

    def bulk_operation(self, operation, entities=None, relationships=None):
        """
        Perform a bulk operation (CREATE, UPDATE, DELETE) on entities or relationships.

        :param operation: "CREATE", "UPDATE", or "DELETE"
        :param entities: List of entities (for entity-related operations)
        :param relationships: List of relationships (for relationship-related operations)
        """
        if not entities and not relationships:
            raise ValueError("Either entities or relationships must be provided.")

        data = {"operation": operation}
        if entities:
            data["entities"] = entities
        if relationships:
            data["relationships"] = relationships

        return self.make_request("POST", "/ems/bulk", data=data)

    def create_entity(self, entities):
        """Create a new entity."""
        return self.bulk_operation("CREATE", entities=entities)

    def update_entity(self, entities):
        """Update an existing entity."""
        return self.bulk_operation("UPDATE", entities=entities)

    def create_relation(self, relationships):
        """Create a new relationship."""
        return self.bulk_operation("CREATE", relationships=relationships)

    def delete_relation(self, relationships):
        """Delete a relationship."""
        return self.bulk_operation("DELETE", relationships=relationships)
