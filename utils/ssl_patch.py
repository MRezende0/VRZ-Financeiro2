import os
import ssl
import urllib3
import requests
import functools

def patch_ssl():
    """
    Monkey patch SSL para resolver problemas de certificado.
    Esta é uma solução robusta para o problema de SSL.
    """
    # Criar um contexto SSL personalizado que ignora verificações de certificado
    old_merge_environment_settings = requests.Session.merge_environment_settings

    @functools.wraps(old_merge_environment_settings)
    def new_merge_environment_settings(self, url, proxies, stream, verify, cert):
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings

    requests.Session.merge_environment_settings = new_merge_environment_settings

    # Desabilitar avisos de SSL inseguro
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Configurar contexto SSL personalizado
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Configurar variável de ambiente para ignorar verificação SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'
