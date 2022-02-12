from docassemble.base.util import get_config, space_to_underscore, Individual
from docassemble.AssemblyLine.al_document import ALDocument, ALDocumentBundle
import os
from webdav3.client import Client
from datetime import datetime
from typing import Union

__all__ = ["publish_to_webdav", "get_new_bundle_path_name"]

def get_new_bundle_path_name(bundle:ALDocumentBundle, user:Union[Individual, str]) -> str:
  """Create a folder name from the bundle and user provided. Folder name will
  have a datetime prefix with iso compact format."""
  current_datetimestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
  if isinstance(user, Individual):
    if hasattr(user.name, 'last'):
      user_string = user.name.lastfirst()                
    else:
      user_string = user.name.first
  else:
    user_string = user
  return space_to_underscore(f"{os.path.splitext(bundle.filename)[0]}_{current_datetimestamp}_{user_string}")

def publish_to_webdav(bundle:ALDocumentBundle, 
                      path:str = None,
                      new_folder:str = None,
                      key:str = "final",
                      config:str = "webdav",
                      webdav_hostname:str = None, 
                      webdav_login:str = None,
                      webdav_password:str = None) -> None:
  """Uploads the contents of an ALDocumentBundle to a webdav server.
  Optionally, specify the key and either the name of a dictionary in the
  docassemble global config or the webdav hostname, username, and password of a 
  webdav server.
  May raise exceptions if the credentials or path are incorrect.
  
  Example configuration entry:
  ```
  webdav:
    webdav_hostname: https://some.webdav_server.com/dav
    webdav_login: some_username
    webdav_password: some_password
    path: /files/user/path
  ```  
  """
  # Prevent Docassemble from running this multiple times (idempotency)
  for document in bundle:
    document[key].path()
    document.filename
    
  if not webdav_login and config:
    config = get_config(config, {})
    default_path = config.get("default_path", "/")
  else:
    config = {"webdav_hostname": webdav_hostname,
              "webdav_login": webdav_login,
              "webdav_password": webdav_password
             }
    default_path = "/"
  
  if not path:
    path = default_path
    
  client = Client(config)
  if new_folder:
    path = os.path.join(path, new_folder)
    client.mkdir(path)
  
  for document in bundle:
    file_path = document[key].path()
    base_name = os.path.splitext(os.path.basename(document.filename))[0]
    base_extension = os.path.splitext(file_path)[1]
    client.upload_sync(remote_path=os.path.join(path, base_name + base_extension), local_path = file_path)
      
  
  