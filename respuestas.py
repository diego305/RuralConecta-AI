def generar_respuesta(categoria, urgencia_nlp=False):
    if urgencia_nlp:
        return (
            "Estimado/a ciudadano/a rural, su reporte ha sido clasificado con prioridad URGENTE. Se ha derivado de inmediato a las cuadrillas de emergencia rural para su atención prioritaria.",
            "¡Hola! Detectamos que tu caso es urgente 🚨. Ya enviamos la alerta a los equipos de emergencias rurales para coordinar la asistencia inmediata en tu paraje."
        )
        
    respuestas = {
        "Red Vial Rural y Caminos": (
            "Estimado/a, hemos recibido su reporte sobre el estado de la red vial rural. Su solicitud fue incorporada al plan operativo de mantenimiento con motoniveladoras y maquinaria pesada.",
            "¡Hola! Ya anotamos tu reporte por el camino rural 🚜. Lo sumamos a la programación de la cuadrilla de vialidad para que pasen a repasar y arreglar la zona. ¡Muchas gracias!"
        ),
        "Agua Potable Rural y Riego": (
            "Estimado/a vecino/a, su solicitud relativa a la red de agua potable/riego rural ha sido derivada a la Dirección de Recursos Hídricos y Agua Potable para su pronta inspección.",
            "¡Hola! Recibimos tu aviso por el agua potable/riego 💧. El equipo técnico de hídrica ya está al tanto para revisar bombas y conexiones en tu paraje. ¡Gracias por avisar!"
        ),
        "Electrificación y Alumbrado Rural": (
            "Estimado/a, se ha registrado el reclamo por inconvenientes en la red eléctrica o alumbrado rural. Se notificó a la Dirección de Electrotecnia para programar la reparación.",
            "¡Hola! Registramos tu reclamo por el servicio eléctrico/alumbrado 💡. El equipo de electromecánica pasará a verificar postes y luminarias en la zona. ¡Saludos!"
        ),
        "Residuos y Limpieza Rural": (
            "Estimado/a, su reporte referente a la recolección o acopio de residuos rurales ha sido derivado a la Dirección de Servicios Ambientales para coordinar el retiro.",
            "¡Hola! Tomamos nota sobre el punto de acopio o residuos 🗑️. Vamos a coordinar el recorrido del camión para limpiar el sector a la brevedad. ¡Gracias por colaborar!"
        ),
        "Zoonosis y Control de Plagas Rurales": (
            "Estimado/a, su informe ha sido elevado al área de Zoonosis y Sanidad Animal para realizar las tareas de control, prevención y operativos en el paraje.",
            "¡Hola! Pasamos tu reporte al equipo de Zoonosis y Sanidad 🐾. Estaremos coordinando el operativo correspondiente en la zona rural. ¡Gracias por escribirnos!"
        ),
        "Medio Ambiente y Recurso Forestal": (
            "Estimado/a vecino/a, su aviso sobre despeje forestal o prevención ambiental fue derivado a la Dirección de Desarrollo Sustentable y Medio Ambiente.",
            "¡Hola! Registramos tu aviso ambiental 🌳. El personal forestal y ambiental inspeccionará el área para realizar los despejes y controles pertinentes."
        ),
        "Infraestructura Comunitaria Rural": (
            "Estimado/a, la solicitud sobre infraestructura comunitaria o puesto sanitario fue derivada a la Secretaría de Obras y Servicios Rurales para su evaluación.",
            "¡Hola! Tomamos tu pedido para la infraestructura del paraje 🏛️. El área de obras públicas rurales ya tiene el reporte para incluirlo en los trabajos de mantenimiento."
        ),
        "Convivencia y Mediación Rural": (
            "Estimado/a ciudadano/a, su caso ha sido derivado al Centro de Mediación y Convivencia Rural para coordinar una instancia de diálogo voluntario.",
            "¡Hola! Pasamos tu solicitud al equipo de Mediación Rural 🤝. Un mediador se comunicará para colaborar en la resolución pacífica de la situación."
        ),
        "OTROS": (
            "Estimado/a ciudadano/a, gracias por comunicarse con la Central de Atención Rural. Su solicitud será procesada y asignada al área competente.",
            "¡Hola! Gracias por comunicarte con RuralConecta 😊. Ya registramos tu consulta y un operador la derivará al área municipal correspondiente."
        )
    }
    
    return respuestas.get(categoria, respuestas["OTROS"])
