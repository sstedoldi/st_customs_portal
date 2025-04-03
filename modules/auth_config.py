import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

def auth_config():
    with open("../run/secrets/portal_users") as file:
        auth = yaml.load(file, Loader=SafeLoader)

    # Pre-hashing all plain text passwords once
    stauth.Hasher.hash_passwords(auth['credentials'])

    authenticator = stauth.Authenticate(
        auth['credentials'],
        auth['cookie']['name'],
        auth['cookie']['key'],
        auth['cookie']['expiry_days'],
        auto_hash = False
    )

    return authenticator#, auth

# def auth_update(auth):
#     with open('auth_.yaml', 'w') as file:
#         yaml.dump(auth, file, default_flow_style=False, allow_unicode=True)