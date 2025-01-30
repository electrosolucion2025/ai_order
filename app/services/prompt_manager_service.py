async def prepare_prompt(context: dict) -> str:
    """
    Prepara el prompt para el usuario.
    """
    prompt = "Eres Juan, un amable camarero. Este es tu menú en formato JSON:\n"
    prompt += f"{context.get('menu', {})}\n\n"
    prompt += "Aquí está el historial de la conversación:\n"
    for entry in context.get("conversation", []):
        prompt += f"Usuario: {entry['user']}\nBot: {entry['bot']}\n"
    return prompt
