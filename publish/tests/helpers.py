def _get_rendered_content(response):
    content = getattr(response, 'rendered_content', None)
    if content is not None:
        return content
    return response.content