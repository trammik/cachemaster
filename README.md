# cachemaster

### Pre-requirements:
- python3.8

#### Installation
In repo directory perform this instruction step-by-step

1. Create venv
```bash 
python3.8 -m venv venv_cachemaster
```
2. Activate venv
```bash 
source venv_cachemaster/bin/activate
```
3. Update pip, install requirements
```bash 
(venv_cachemaster) pip install -U pip
(venv_cachemaster) pip install -r requirements.txt
```
4. Run dummy webserver (in different terminal)
```bash 
(venv_cachemaster) python dummy_server.py
```
5. Run tests
```bash 
(venv_cachemaster) pytest test_cache.py
```
