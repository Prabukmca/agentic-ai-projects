import pkgutil, importlib, langchain

def find_serpapi_symbols():
    matches = []
    for finder, name, ispkg in pkgutil.walk_packages(langchain.__path__, prefix='langchain.'):
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        if hasattr(mod, 'SerpAPIWrapper'):
            matches.append((name, 'has attribute SerpAPIWrapper'))
        for attr in dir(mod):
            if 'SerpAPI' in attr or 'serpapi' in attr.lower():
                matches.append((name, attr))
    return matches

if __name__ == '__main__':
    print('langchain version ->', getattr(langchain, '__version__', 'unknown'))
    m = find_serpapi_symbols()
    if not m:
        print('No SerpAPIWrapper or serpapi-named attributes found in langchain package')
    else:
        for item in m:
            print(item)
