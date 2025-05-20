                            {% if piece.fichier %}
                                {% with piece.fichier.url|lower as file_url %}
                                    {% if ".pdf" in file_url %}
                                        <iframe src="{{ piece.fichier.url }}" width="100%" height="600" class="rounded border"></iframe>
                                        <p class="mt-4 text-center text-sm text-muted-foreground">
                                            Aperçu PDF du document : {{ piece.titre }}
                                        </p>
                                    {% elif ".jpg" in file_url or ".jpeg" in file_url or ".png" in file_url or ".gif" in file_url %}
                                        <img src="{{ piece.fichier.url }}" alt="{{ piece.titre }}" class="max-h-96 rounded-lg object-contain shadow-sm" />
                                        <p class="mt-4 text-center text-sm text-muted-foreground">
                                            Aperçu image du document : {{ piece.titre }}
                                        </p>
                                    {% elif ".doc" in file_url or ".docx" in file_url or ".xls" in file_url or ".xlsx" in file_url or ".ppt" in file_url or ".pptx" in file_url %}
                                        <iframe src="https://view.officeapps.live.com/op/view.aspx?src={{ request.build_absolute_uri(piece.fichier.url)|urlencode }}" width="100%" height="600" frameborder="0"></iframe>
                                        <p class="mt-4 text-center text-sm text-muted-foreground">
                                            Aperçu Office Online du document : {{ piece.titre }}
                                        </p>
                                    {% else %}
                                        <iframe src="https://docs.google.com/viewer?url={{ request.build_absolute_uri(piece.fichier.url)|urlencode }}&embedded=true" width="100%" height="600" frameborder="0"></iframe>
                                        <p class="mt-4 text-center text-sm text-muted-foreground">
                                            Aperçu Google Docs du document : {{ piece.titre }}
                                        </p>
                                    {% endif %}
                                {% endwith %}
                            {% else %}
                                <img src="{% static 'img/placeholder.svg' %}" alt="Aperçu" class="max-h-96 rounded-lg object-contain shadow-sm" />
                                <p class="mt-4 text-center text-sm text-muted-foreground">
                                    Aucun fichier associé à cette pièce.
                                </p>
                            {% endif %}
                        </div>