Clases:
-clase para el manager que ofrece la api del groupmembership.
-clase abstracta o con algunos metodos abstractos que define al miembro del grupo.
-clase que especializa a la última para los miembros con TOM mediante secuenciador.
-clase que especializa a la penúltima para los miembros con TOM mediante Lamport.

Modelo TOM con secuenciador:
El secuenciador se encarga de dar los timestamps a los miembros antes de que estos envien los mensajes por multicast.
El secuenciador es uno de los miembros.
El miembro que desempeña este rol es siempre aquel cuyo identificador es mayor con respecto a los otros miembros.
Cuando cae un secuenciador se realiza una nueva elección mediante la misma regla anterior. (Preguntar si la elección tiene que conllevar ack's entre los miembros restantes)
Cada miembro manda un mensaje por multicast junto con el timestamp que le ha otorgado el secuenciador previamente.
En cada miembro, dichos mensajes se guardan en una cola hasta que les toque ser procesados según su timestamp.
Si el siguiente mensaje por orden de timestamp no es recibido por alguno de los peers está ha de esperar su llegada a menos que el gestor le indique que el emisario de este ha caido.
Cuando se de el caso que un miembro ha caido y este es posesor de uno de los timestamps no procesados todos los otros miembros han de ser notificados de su caída y han de desechar dicho timestamp.

