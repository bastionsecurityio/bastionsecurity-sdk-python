import os,json,uuid,hashlib
from bastion import BastionClient,BastionError
c=json.load(open(os.environ.get('BASTION_QA_SESSION','/tmp/bastion-sdk-qa-session.json')))
assert c['endpoint'].startswith(('http://localhost:','http://127.0.0.1:')),'Local QA only'
with BastionClient(c['site_key'],c['secret'],c['endpoint']) as client:
    fp=client.fingerprint({'canvas_hash':'python-sdk-e2e','platform':'MacIntel','user_agent':'Mozilla/5.0 Chrome/130.0','language':'en-US','languages':['en-US']})
    assert fp['token'] and fp['expires_at']
    request={'token':fp['token'],'context':{'event_type':'login','account_id':'python-sdk-e2e','login_succeeded':False},'idempotency_key':str(uuid.uuid4())}
    decision=client.verify(request);assert client.verify(request)['request_id']==decision['request_id'];assert isinstance(decision['signals'],list)
    assert client.classify(fp['token'],{'event_type':'signup','account_id':'python-sdk-classify'})['request_id']
    assert client.track('checkout',{'account_id':'python-sdk-track','order_amount':4,'payment_hash':'python-test-card'},fp['token'])['request_id']
    result=client.batch([dict(request,idempotency_key=str(uuid.uuid4())),{'context':{'event_type':'unsupported','account_id':'invalid'}}]);assert result['accepted']==1 and result['results'][1]['status']==400
    try:
        with BastionClient(c['site_key'],'wrong',c['endpoint']) as bad:bad.verify(request)
        raise AssertionError('Invalid auth accepted')
    except BastionError as error:assert error.status==401
    challenge=client.create_challenge(4);nonce=0
    def base36(n):
        alphabet='0123456789abcdefghijklmnopqrstuvwxyz';out=''
        while n:n,r=divmod(n,36);out=alphabet[r]+out
        return out or '0'
    while not hashlib.sha256((challenge['prefix']+base36(nonce)).encode()).hexdigest().startswith('0'*challenge['difficulty']):nonce+=1
    assert client.verify_challenge(challenge['challenge_id'],base36(nonce))['valid'] is True
    try:client.verify_challenge(challenge['challenge_id'],base36(nonce));raise AssertionError('Replay accepted')
    except BastionError as error:assert error.status==400
print('PASS: Python SDK real fingerprint, scoring, deduplication, classify/track, partial batch, auth failure and proof/replay checks.')
