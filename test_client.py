import hashlib, hmac, unittest
import httpx
from bastion import BastionClient, BastionError, verify_webhook
class ClientTests(unittest.TestCase):
    def test_contract_and_retry(self):
        sent=[]
        def handler(request):
            self.assertEqual(request.url.path, '/api/antibot/verify')
            self.assertEqual(request.headers['X-Site-Key'], 'public')
            self.assertEqual(request.headers['X-Secret-Key'], 'private')
            sent.append(request.content)
            return httpx.Response(503, json={'message':'retry'}) if len(sent)==1 else httpx.Response(201,json={'success':True,'data':{'action':'block','signals':[{'rule':'card_testing'}]}})
        client=BastionClient('public','private')
        client.http.close();client.http=httpx.Client(transport=httpx.MockTransport(handler),headers={'X-Site-Key':'public','X-Secret-Key':'private'})
        result=client.verify({'context':{'event_type':'checkout','account_id':'a'},'environment':{'nonce':'test'}})
        self.assertEqual(sent[0],sent[1]);self.assertEqual(result['signals'][0]['rule'],'card_testing');client.close()
    def test_invalid_auth_is_not_retried(self):
        sent=[]
        def handler(request):
            sent.append(request);return httpx.Response(401,json={'message':'Invalid site keys'})
        client=BastionClient('public','private');client.http.close();client.http=httpx.Client(transport=httpx.MockTransport(handler))
        with self.assertRaises(BastionError) as caught: client.verify({'context':{'event_type':'login','account_id':'a'}})
        self.assertEqual(caught.exception.status,401);self.assertEqual(len(sent),1);client.close()
    def test_webhook(self):
        body='{"text":"fraud 🚨"}';stamp=12345;secret='secret';sig='t=12345,v1='+hmac.new(secret.encode(),f'{stamp}.{body}'.encode(),hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook(secret,body,sig,now=stamp));self.assertFalse(verify_webhook(secret,body+' ',sig,now=stamp));self.assertFalse(verify_webhook(secret,body,sig,now=stamp+301))
if __name__=='__main__':unittest.main()
