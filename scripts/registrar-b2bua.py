import sys
import KSR as KSR

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

    # Function called for REQUEST messages received 
    def ksr_request_route(self, msg):
        
        # Handle PIN Validation MESSAGE
        if (msg.Method == "MESSAGE"):
            # Use $rU and $rd to match 'validar@acme.pt'
            r_user = KSR.pv.get("$rU")
            r_domain = KSR.pv.get("$rd")

            if (r_user == "validar" and r_domain == "acme.pt"):
                # Use x.modf to force get the body safely if $rb fails
                body = KSR.pv.get("$rb")
                    
                if body is None:
                    KSR.err("MESSAGE: Body is null. Is textops module loaded?\n")
                    KSR.sl.send_reply(400, "Missing PIN Body")
                    return 1

                pin = str(body).strip()
                KSR.info("PIN Received: [" + pin + "] from " + str(KSR.pv.get("$fu")) + "\n")

                if (pin == "0000"):
                    KSR.info("PIN Validation Successful\n")
                    KSR.sl.send_reply(200, "OK - PIN Valid")
                    return 1
                else:
                    KSR.info("PIN check failed: " + pin + "\n")
                    KSR.sl.send_reply(403, "Forbidden - Wrong PIN")
                    return 1
            else:
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
            
            pin = str(body).strip()

            # A special destination with the objective of failing...
            if (KSR.pv.get("$tu") == "sip:nobody@acme.operador"):       # To-URI for failing
                KSR.pv.sets("$ru", "sip:nobody@sipnet.alice:9999") # R-URI replacement to a new destination
                
                # Definition of on_failure for INVITE
                KSR.tm.t_relay()   # Forwarding using transaction mode
                return 1                

            if (KSR.pv.get("$td") != "acme.operador"):       # Check if To domain is sipnet.a
#                KSR.forward()       # Forwarding to a different network using statless mode
                KSR.tm.t_relay()   # Forwarding using transaction mode
                KSR.rr.record_route()  # Add Record-Route header
                return 1

            if (KSR.pv.get("$td") == "acme.operador" or pin == "0000"):             # Check if To domain is sipnet.a (unnecessary duplicate)
                if (KSR.registrar.lookup("location") == 1):   # Check if registered
#                    KSR.info("  lookup changed R-URI to : " + KSR.pv.get("$ru") +"\n")
#                    KSR.forward()       # Forwarding to UA contact using statless mode
                    KSR.tm.t_relay()   # Forwarding using transaction mode
                    KSR.rr.record_route()  # Add Record-Route header
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