import sys
import KSR as KSR

body = ""
r_user = ""
r_domain = ""
# Mandatory function - module initiation
def mod_init():
    KSR.info("===== from Python mod init\n")
    return kamailio()

class kamailio:
    # Mandatory function - Kamailio class initiation
    def __init__(self):
        KSR.info('===== kamailio.__init__\n')

    # Mandatory function - Kamailio subprocesses
    def child_init(self, rank):
        KSR.info('===== kamailio.child_init(%d)\n' % rank)
        return 0

    r_user = KSR.pv.get("$rU")
    r_domain = KSR.pv.get("$rd")
    body = KSR.pv.get("$rb")
    # Function called for REQUEST messages received 
    def ksr_request_route(self, msg):
        
        # Handle Instant Messages (SIP MESSAGE)
        if (msg.Method == "MESSAGE"):
            
            # 1. SPECIAL CASE: PIN Validation Service
            # We must check this FIRST. If we relay this, it will timeout (408).
            r_user = KSR.pv.get("$rU")
            r_domain = KSR.pv.get("$rd")

            if (r_user == "validar" and r_domain == "acme.pt"):
                body = KSR.pv.get("$rb")
                
                # Check if body is empty
                if body is None:
                    KSR.sl.send_reply(400, "Missing PIN")
                    return 1

                pin = str(body).strip()
                KSR.info("PIN Received: " + pin + "\n")

                if (pin == "0000"):
                    KSR.sl.send_reply(200, "OK - PIN Valid")
                    return 1
                else:
                    KSR.sl.send_reply(403, "Forbidden - Wrong PIN")
                    return 1

            # 2. NORMAL CHAT: Relay between local users (Alice <-> Bob)
            # We only allow relaying if the domain is OUR domain (acme.operador)
            if (KSR.pv.get("$td") == "acme.operador"):
                if (KSR.registrar.lookup("location") == 1):
                    KSR.tm.t_relay()
                    return 1
                else:
                    KSR.sl.send_reply(404, "User Not Found")
                    return 1

            # 3. BLOCK EVERYTHING ELSE
            # If it's not the validation service AND not a local user, reject it.
            # Do NOT use t_relay() here, or you will get 408 Timeout.
            KSR.sl.send_reply(403, "Forbidden - Wrong destination")
            return 1

        # Working as a Registrar server
        if  (msg.Method == "REGISTER"):
            domain = KSR.pv.get("$td") # <--- ALTERAÇÃO: Obter o domínio de destino ($td)

            KSR.info("REGISTER R-URI: " + KSR.pv.get("$ru") + "\n")      # Obtaining values via Pseudo-variables (pv)
            KSR.info("            To: " + KSR.pv.get("$tu") +
                           " Contact: " + KSR.hdr.get("Contact") +
                           " Domain: " + domain + "\n") # <--- ALTERAÇÃO: Adicionar log do domínio

            # === Lógica de verificação de domínio para REGISTO ===
            if (domain == "acme.operador"): # <--- ALTERAÇÃO: Permitir registo SÓ se o domínio for "acme.operador"
                KSR.info("Domain check passed for acme.operador. Saving location.\n")
                KSR.registrar.save('location', 0)                            # Calling Kamailio "registrar" module
                return 1
            else:
                KSR.info("Domain check failed. Rejecting registration for domain: " + domain + "\n")
                KSR.sl.send_reply(403, "Forbidden Domain") # <--- ALTERAÇÃO: Rejeitar registo com 403 Forbidden
                return 1

        # Working as a Redirect server
        if (msg.Method == "INVITE"):                      
            KSR.info("INVITE R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("        From: " + KSR.pv.get("$fu") +
                              " To: " + KSR.pv.get("$tu") +"\n")
              

            if (KSR.pv.get("$td") != "acme.operador"):       # Check if To domain is sipnet.a
#                KSR.forward()       # Forwarding to a different network using statless mode
                KSR.rr.record_route()  # Add Record-Route header
                #KSR.tm.t_relay()    # Forwarding using transaction mode
                KSR.sl.send_reply(403, "Forbidden - Wrong destination")
                return 1

            if (KSR.pv.get("$td") == "acme.operador"):             # Check if To domain is sipnet.a (unnecessary duplicate)
                if (KSR.registrar.lookup("location") == 1):   # Check if registered
#                    KSR.info("  lookup changed R-URI to : " + KSR.pv.get("$ru") +"\n")
#                    KSR.forward()       # Forwarding to UA contact using statless mode
                    KSR.rr.record_route()  # Add Record-Route header
                    KSR.tm.t_relay()  # Forwarding using transaction mode
                    return 1
                else:
                    KSR.sl.send_reply(404, "Not found")
                    return 1

        if (msg.Method == "ACK"):
            KSR.info("ACK R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.rr.loose_route()  # In case there are Record-Route headers
            KSR.registrar.lookup("location")
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "BYE"):
            KSR.info("BYE R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.rr.loose_route()    # In case there are Record-Route headers
            KSR.registrar.lookup("location")
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "CANCEL"):
            KSR.info("CANCEL R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.rr.loose_route()    # In case there are Record-Route headers
            KSR.registrar.lookup("location")
            KSR.tm.t_relay()
            return 1

        # If this part is reached then Method is not allowed
        KSR.sl.send_reply(403, "Forbiden method")
        return 1

    # Function called for REPLY messages received
    def ksr_reply_route(self, msg):
        KSR.info("===== reply_route - from kamailio python script: ")
        KSR.info("  Status is:"+ str(KSR.pv.get("$rs")) + "\n")
        return 1

    # Function called for messages sent/transit
    def ksr_onsend_route(self, msg):
        KSR.info("===== onsend route - from kamailio python script:")
        KSR.info("   %s\n" %(msg.Type))
        return 1