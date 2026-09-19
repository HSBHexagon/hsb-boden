import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
SID = "1W-NjwEq0UhDo2TaeS-2qp_qit4YFMz6k-IqKHlPpHmg"
def services(profile="cherinojoel"):
    tok = json.load(open(f"/Users/joelcherinodiaz/.config/google-workspace-mcp/profiles/{profile}/tokens.json"))
    cred = json.load(open("/Users/joelcherinodiaz/.config/google-workspace-mcp/credentials.json"))
    c = cred.get("installed") or cred.get("web") or cred
    creds = Credentials(token=tok.get("access_token"), refresh_token=tok.get("refresh_token"),
                        token_uri="https://oauth2.googleapis.com/token", client_id=c["client_id"],
                        client_secret=c["client_secret"], scopes=tok.get("scope","").split())
    return build("sheets","v4",credentials=creds,cache_discovery=False), build("drive","v3",credentials=creds,cache_discovery=False)
def col(i):
    s=""; i+=1
    while i: i,r=divmod(i-1,26); s=chr(65+r)+s
    return s
