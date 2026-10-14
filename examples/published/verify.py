import os
from bastion import BastionClient, BastionError

def verify_request(request):
    with BastionClient(
        site_key=os.environ["BASTION_SITE_KEY"],
        secret=os.environ["BASTION_SECRET_KEY"],
        endpoint=os.environ.get("BASTION_ENDPOINT", "https://api-production-761a5.up.railway.app/api/antibot"),
    ) as client:
        decision = client.verify(request)
        return {"allowed": decision["action"] == "allow", "decision": decision}
# Let API errors stop the approval path; handle them in your app.
