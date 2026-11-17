"""Synthetic-only provider for the API starter; never used by production."""
class SyntheticProvider:
    available = True
    def __init__(self):
        self.calls = 0
    def resolve(self, text):
        self.calls += 1
        candidates = []
        if 'empty' not in text:
            for version in ('v1', 'v2'):
                identity = {'system_version':version, 'order_id':12345}
                candidates.append({**identity, 'created':'2026-02-01', 'citation':{'type':'sql', 'source_id':'sql:synthetic', 'ref':'synthetic_orders', 'locator':'order:row', 'record_key':identity}})
        return {'status':'found' if candidates else 'not_found', 'source_version':'synthetic-v1', 'received_date':'2026-03-01', 'candidates':candidates}
    def revalidate(self, version, received, identity):
        return self.resolve('order 12345')
