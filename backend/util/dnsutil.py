#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import dns
import dns.name
import dns.query
import dns.resolver
from dns.exception import Timeout
from dns.resolver import NoAnswer


def get_authoritative_nameserver(domain):
  try:
    n = dns.name.from_text(domain)
  except:
    return None, 'Invalid domain name'

  depth = 2
  default = dns.resolver.get_default_resolver()
  nameserver = default.nameservers[0]

  authority = None
  last = False
  while not last:
    prefix, sub = n.split(depth)
    last = str(prefix) == '@'

    query = dns.message.make_query(sub, dns.rdatatype.NS)
    response = dns.query.udp(query, nameserver)

    rcode = response.rcode()
    if rcode != dns.rcode.NOERROR:
      if rcode == dns.rcode.NXDOMAIN:
        return None, 'Domain could not be found'
      else:
        return None, 'Error %s' % dns.rcode.to_text(rcode)

    rrset = None
    if len(response.authority) > 0:
      rrset = response.authority[0]
    else:
      rrset = response.answer[0]

    rr = rrset[0]
    if rr.rdtype not in (dns.rdatatype.SOA, dns.rdatatype.CNAME):
      authority = rr.target
      nameserver = default.query(authority).rrset[0].to_text()

    depth += 1

  if authority:
    return nameserver, None

  return None, 'Domain could not be found'


def get_cname_for_domain(domain):
  authority, err = get_authoritative_nameserver(domain)
  if err:
    return None, err

  query = dns.message.make_query(domain, dns.rdatatype.CNAME)
  try:
    response = dns.query.tcp(query, authority, timeout=1)

  except Timeout:
    return None, 'Could not connect to nameserver for that domain'

  except NoAnswer:
    return None, 'Domain could not be found'

  if response and response.answer:
    for answer in response.answer:
      return str(answer[0].target), None

  return None, 'CNAME is missing for the specified domain'
