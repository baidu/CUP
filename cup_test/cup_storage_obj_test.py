#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:

"""
from cup.storage import obj
s3 = obj.S3ObjectSystem(
    {
        'ak': 'dQL2wNqjcerNJsrobLbK', 
        'sk': 'hfkWQdDB8sMsimgIqZORBsWIZyPzahJtToKZoLCz', 
        'endpoint': 'https://127.0.0.1:9000', 'bucket':'messager', 
        'verify': 'xx.crt'
    }
)
s3.put('/minio-testa', '/Users/didi/minio-test')
print(s3.head('/minio-testa'))
print(s3.delete('/minio-test'))

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
