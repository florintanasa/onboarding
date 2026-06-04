import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

PROIECT_PATH = str(Path.cwd())


def get_project_name(settings_path: Path = Path("settings.gradle")) -> str | None:
    text = settings_path.read_text(encoding="utf-8")
    # caută rootProject.name = 'name' sau "name"
    m = re.search(r"""rootProject\.name\s*=\s*(['"])(.*?)\1""", text)
    return m.group(2) if m else None


PROJECT = get_project_name()
project_name = (PROJECT or "").lower()


def get_company_name(settings_path: Path = Path("build.gradle")) -> str | None:
    text = settings_path.read_text(encoding="utf-8")
    # caută group = 'com.company' sau "com.company"
    m = re.search(r"""group\s*=\s*(['"])(.*?)\1""", text)
    return m.group(2) if m else None


COMPANY = get_company_name() or ""
company_path = COMPANY.replace(".", "/")


def get_fields(fi):
    return [f.split(":", 1) if ":" in f else (f, "String") for f in fi.split()]


def gen_entity_mechanic(n, fi):
    print("Generating Entity " + n + " mechanically (Zero AI, 100% Reliable)...")

    fields_list = get_fields(fi)

    # 1. Construim sectiunea de declarare a campurilor specifice
    java_fields = ""
    is_first_text_field = True

    for f_name, f_type in fields_list:
        annotations = ""
        # Punem @InstanceName pe primul camp de tip String
        if f_type == "String" and is_first_text_field:
            annotations += "    @InstanceName\n"
            is_first_text_field = False

        annotations += '    @Column(name = "' + f_name.upper() + '")\n'
        java_fields += annotations + "    private " + f_type + " " + f_name + ";\n\n"

    # 2. Construim sectiunea de Getter-e si Setter-e pentru campurile specifice
    java_methods = ""
    for f_name, f_type in fields_list:
        cap_name = f_name[0].upper() + f_name[1:]

        # Getter
        java_methods += "    public " + f_type + " get" + cap_name + "() {\n"
        java_methods += "        return " + f_name + ";\n"
        java_methods += "    }\n\n"

        # Setter
        java_methods += (
            "    public void set" + cap_name + "(" + f_type + " " + f_name + ") {\n"
        )
        java_methods += "        this." + f_name + " = " + f_name + ";\n"
        java_methods += "    }\n\n"

    # 3. Asamblam structura completa a clasei Java conform Jmix Studio
    clasa_completa = (
        f"package {COMPANY}.{project_name}.entity;\n\n"
        "import io.jmix.core.entity.annotation.JmixGeneratedValue;\n"
        "import io.jmix.core.metamodel.annotation.InstanceName;\n"
        "import io.jmix.core.metamodel.annotation.JmixEntity;\n"
        "import jakarta.persistence.*;\n"
        "import java.math.BigDecimal;\n"
        "import java.time.LocalDate;\n"
        "import java.time.LocalDateTime;\n"
        "import java.time.OffsetDateTime;\n"
        "import java.util.UUID;\n"
        "import org.springframework.data.annotation.CreatedBy;\n"
        "import org.springframework.data.annotation.CreatedDate;\n"
        "import org.springframework.data.annotation.LastModifiedBy;\n"
        "import org.springframework.data.annotation.LastModifiedDate;\n\n"
        "@JmixEntity\n"
        '@Table(name = "' + n.upper() + '")\n'
        "@Entity\n"
        "public class " + n + " {\n\n"
        "    @Id\n"
        '    @Column(name = "ID", nullable = false)\n'
        "    @JmixGeneratedValue\n"
        "    private UUID id;\n\n"
        '    @Column(name = "VERSION", nullable = false)\n'
        "    @Version\n"
        "    private Integer version;\n\n"
        "    @CreatedBy\n"
        '    @Column(name = "CREATED_BY")\n'
        "    private String createdBy;\n\n"
        "    @CreatedDate\n"
        '    @Column(name = "CREATED_DATE")\n'
        "    private OffsetDateTime createdDate;\n\n"
        "    @LastModifiedBy\n"
        '    @Column(name = "LAST_MODIFIED_BY")\n'
        "    private String lastModifiedBy;\n\n"
        "    @LastModifiedDate\n"
        '    @Column(name = "LAST_MODIFIED_DATE")\n'
        "    private OffsetDateTime lastModifiedDate;\n\n"
        "    // --- Specific Fields ---\n"
        + java_fields
        + "    // --- System Getters and Setters ---\n"
        "    public UUID getId() {\n        return id;\n    }\n\n"
        "    public void setId(UUID id) {\n        this.id = id;\n    }\n\n"
        "    public Integer getVersion() {\n        return version;\n    }\n\n"
        "    public void setVersion(Integer version) {\n        this.version = version;\n    }\n\n"
        "    public String getCreatedBy() {\n        return createdBy;\n    }\n\n"
        "    public void setCreatedBy(String createdBy) {\n        this.createdBy = createdBy;\n    }\n\n"
        "    public OffsetDateTime getCreatedDate() {\n        return createdDate;\n    }\n\n"
        "    public void setCreatedDate(OffsetDateTime createdDate) {\n        this.createdDate = createdDate;\n    }\n\n"
        "    public String getLastModifiedBy() {\n        return lastModifiedBy;\n    }\n\n"
        "    public void setLastModifiedBy(String lastModifiedBy) {\n        this.lastModifiedBy = lastModifiedBy;\n    }\n\n"
        "    public OffsetDateTime getLastModifiedDate() {\n        return lastModifiedDate;\n    }\n\n"
        "    public void setLastModifiedDate(OffsetDateTime lastModifiedDate) {\n        this.lastModifiedDate = lastModifiedDate;\n    }\n\n"
        "    // --- Specific Getters and Setters ---\n" + java_methods + "}\n"
    )

    # 4. Scriem fisierul direct in structura corecta a proiectului
    td = PROIECT_PATH + f"/src/main/java/{company_path}/{project_name}/entity"
    if not os.path.exists(td):
        os.makedirs(td)

    java_path = td + "/" + n + ".java"
    open(java_path, "w", encoding="utf-8").write(clasa_completa)
    print("✨ Entity mecanic salvat cu succes in: " + java_path)


def gen_list_ui(n, fi):
    print("Generating List UI Mechanically...")
    j = (
        "package " + COMPANY + "." + project_name + ".view." + n.lower() + ";\n"
        "import " + COMPANY + "." + project_name + ".entity." + n + ";\n"
        "import " + COMPANY + "." + project_name + ".view.main.MainView;\n"
        "import com.vaadin.flow.router.Route;\n"
        "import io.jmix.flowui.view.*;\n\n"
        '@Route(value="' + n.lower() + 's", layout=MainView.class)\n'
        '@ViewController(id = "' + n + '.list")\n'
        '@ViewDescriptor(path = "' + n.lower() + '-list-view.xml")\n'
        '@LookupComponent("' + n.lower() + 'sDataGrid")\n'
        '@DialogMode(width = "64em")\n'
        "public class " + n + "ListView extends StandardListView<" + n + "> {}"
    )
    cols = ""
    for name, _ in get_fields(fi):
        cols += '                <column property="' + name + '"/>\n'

    x = (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<view xmlns="http://jmix.io/schema/flowui/view"\n'
        '      title="msg://' + n.lower() + 'ListView.title"\n'
        '      focusComponent="' + n.lower() + 'sDataGrid">\n'
        "    <data>\n"
        '        <collection id="' + n.lower() + 'sDc"\n'
        '                    class="'
        + COMPANY
        + "."
        + project_name
        + ".entity."
        + n
        + '">\n'
        '            <loader id="' + n.lower() + 'sDl" readOnly="true">\n'
        "                <query>\n"
        "                    <![CDATA[select e from " + n + " e]]>\n"
        "                </query>\n"
        "            </loader>\n"
        "        </collection>\n"
        "    </data>\n"
        "    <facets>\n"
        '        <dataLoadCoordinator auto="true"/>\n'
        "        <urlQueryParameters>\n"
        '            <genericFilter component="genericFilter"/>\n'
        '            <pagination component="pagination"/>\n'
        "        </urlQueryParameters>\n"
        "    </facets>\n"
        "    <actions>\n"
        '        <action id="selectAction" type="lookup_select"/>\n'
        '        <action id="discardAction" type="lookup_discard"/>\n'
        "    </actions>\n"
        "    <layout>\n"
        '        <genericFilter id="genericFilter"\n'
        '               dataLoader="' + n.lower() + 'sDl">\n'
        '            <properties include=".*"/>\n'
        "        </genericFilter>\n"
        '        <hbox id="buttonsPanel" classNames="buttons-panel">\n'
        "            <startSlot>\n"
        '                <button id="createButton" action="'
        + n.lower()
        + 'sDataGrid.createAction"/>\n'
        '                <button id="editButton" action="'
        + n.lower()
        + 'sDataGrid.editAction"/>\n'
        '                <button id="removeButton" action="'
        + n.lower()
        + 'sDataGrid.removeAction"/>\n'
        "            </startSlot>\n"
        "            <endSlot>\n"
        '                <simplePagination id="pagination" dataLoader="'
        + n.lower()
        + 'sDl"/>\n'
        "            </endSlot>\n"
        "        </hbox>\n"
        '        <dataGrid id="' + n.lower() + 'sDataGrid"\n'
        '                  width="100%"\n'
        '                  minHeight="20em"\n'
        '                  dataContainer="' + n.lower() + 'sDc"\n'
        '                  columnReorderingAllowed="true">\n'
        "            <actions>\n"
        '                <action id="createAction" type="list_create"/>\n'
        '                <action id="editAction" type="list_edit"/>\n'
        '                <action id="removeAction" type="list_remove"/>\n'
        "            </actions>\n"
        '            <columns  resizable="true">\n' + cols + "            </columns>\n"
        "        </dataGrid>\n"
        '        <hbox id="lookupActions" visible="false">\n'
        '            <button id="selectButton" action="selectAction"/>\n'
        '            <button id="discardButton" action="discardAction"/>\n'
        "        </hbox>\n"
        "    </layout>\n"
        "</view>\n"
    )

    jd = (
        PROIECT_PATH + f"/src/main/java/{company_path}/{project_name}/view/" + n.lower()
    )
    xd = (
        PROIECT_PATH
        + f"/src/main/resources/{company_path}/{project_name}/view/"
        + n.lower()
    )

    if not os.path.exists(jd):
        os.makedirs(jd)
    if not os.path.exists(xd):
        os.makedirs(xd)

    open(jd + "/" + n + "ListView.java", "w", encoding="utf-8").write(j)
    open(xd + "/" + n.lower() + "-list-view.xml", "w", encoding="utf-8").write(x)
    print("✨ List View mecanic salvat!")


def gen_detail_ui(n, fi):
    print("Generating Detail UI Mechanically...")

    # 1. Controller Java pentru ecranul de Detaliu
    j = (
        "package " + COMPANY + "." + project_name + ".view." + n.lower() + ";\n\n"
        "import " + COMPANY + "." + project_name + ".entity." + n + ";\n"
        "import " + COMPANY + "." + project_name + ".view.main.MainView;\n"
        "import com.vaadin.flow.router.Route;\n"
        "import io.jmix.flowui.view.*;\n\n"
        '@Route(value="' + n.lower() + 's/:id", layout=MainView.class)\n'
        '@ViewController(id = "' + n + '.detail")\n'
        '@ViewDescriptor(path = "' + n.lower() + '-detail-view.xml")\n'
        '@EditedEntityContainer("' + n.lower() + 'Dc")\n'
        "public class " + n + "DetailView extends StandardDetailView<" + n + "> {}"
    )

    # 2. Maparea mecanica a campurilor din formular in functie de tipul Java
    flds = ""
    for name, t in get_fields(fi):
        if t == "LocalDate":
            flds += (
                '            <datePicker id="'
                + name
                + 'Field" property="'
                + name
                + '"/>\n'
            )
        elif t == "Boolean":
            flds += (
                '            <checkbox id="'
                + name
                + 'Field" property="'
                + name
                + '"/>\n'
            )
        elif t == "BigDecimal":
            flds += (
                '            <textField id="'
                + name
                + 'Field" property="'
                + name
                + '" width="100%" datatype="decimal"/>\n'
            )
        elif t == "Integer":
            flds += (
                '            <textField id="'
                + name
                + 'Field" property="'
                + name
                + '" width="100%" datatype="int"/>\n'
            )
        elif t == "Long":
            flds += (
                '            <textField id="'
                + name
                + 'Field" property="'
                + name
                + '" width="100%" datatype="long"/>\n'
            )
        elif t == "Double":
            flds += (
                '            <textField id="'
                + name
                + 'Field" property="'
                + name
                + '" width="100%" datatype="double"/>\n'
            )
        else:
            flds += (
                '            <textField id="'
                + name
                + 'Field" property="'
                + name
                + '" width="100%"/>\n'
            )

    # 3. Structura XML nativa conform Jmix Studio
    x = (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<view xmlns="http://jmix.io/schema/flowui/view"\n'
        '      title="msg://' + n.lower() + 'DetailView.title">\n'
        "    <data>\n"
        '        <instance id="' + n.lower() + 'Dc"\n'
        '                    class="'
        + COMPANY
        + "."
        + project_name
        + ".entity."
        + n
        + '">\n'
        '            <fetchPlan extends="_base"/>\n'
        '            <loader id="' + n.lower() + 'Dl"/>\n'
        "        </instance>\n"
        "    </data>\n"
        "    <facets>\n"
        '        <dataLoadCoordinator auto="true"/>\n'
        "    </facets>\n"
        "    <actions>\n"
        '        <action id="saveAction" type="detail_saveClose"/>\n'
        '        <action id="closeAction" type="detail_close"/>\n'
        "    </actions>\n"
        '    <layout expand="form" spacing="true">\n'
        '        <formLayout id="form" dataContainer="' + n.lower() + 'Dc">\n'
        "            <responsiveSteps>\n"
        '                <responsiveStep minWidth="0" columns="1"/>\n'
        '                <responsiveStep minWidth="40em" columns="2"/>\n'
        "            </responsiveSteps>\n" + flds + "        </formLayout>\n"
        '        <hbox id="detailActions" classNames="buttons-panel">\n'
        '            <button id="saveAndCloseButton" action="saveAction"/>\n'
        '            <button id="closeButton" action="closeAction"/>\n'
        "        </hbox>\n"
        "    </layout>\n"
        "</view>\n"
    )

    jd = (
        PROIECT_PATH + f"/src/main/java/{company_path}/{project_name}/view/" + n.lower()
    )
    xd = (
        PROIECT_PATH
        + f"/src/main/resources/{company_path}/{project_name}/view/"
        + n.lower()
    )

    if not os.path.exists(jd):
        os.makedirs(jd)
    if not os.path.exists(xd):
        os.makedirs(xd)

    open(jd + "/" + n + "DetailView.java", "w", encoding="utf-8").write(j)
    open(xd + "/" + n.lower() + "-detail-view.xml", "w", encoding="utf-8").write(x)
    print("✨ Detail View mecanic salvat!")


def update_messages_entity(n, fi):
    print("Generating localization messages for " + n + "...")
    fields_list = get_fields(fi)

    # Definim calea catre cele doua fisiere din proiectul tau Gradle
    base_path = PROIECT_PATH + f"/src/main/resources/{company_path}/{project_name}"
    en_path = base_path + "/messages_en.properties"
    ro_path = base_path + "/messages_ro.properties"

    # 1. Pregatim traducerile pentru limba Engleza (Mecanic)
    en_lines = []
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}={n}")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.id=Id")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.version=Version")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdBy=Created by")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdDate=Created date")
    en_lines.append(
        f"{COMPANY}.{project_name}.entity/{n}.lastModifiedBy=Last modified by"
    )
    en_lines.append(
        f"{COMPANY}.{project_name}.entity/{n}.lastModifiedDate=Last modified date"
    )
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedBy=Deleted by")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedDate=Deleted date")

    for f_name, _ in fields_list:
        # Transforma camelCase in text separat (ex: creditLimit -> Credit limit)
        spaced_name = re.sub(r"(?<!^)(?=[A-Z])", " ", f_name).lower()
        readable_en = spaced_name[0].upper() + spaced_name[1:]
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={readable_en}")

    # Adaugam si titlurile pentru ecranele UI generate anterior
    en_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}ListView.title={n}s"
    )
    en_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}DetailView.title={n} detail"
    )

    # 2. Pregatim traducerile pentru limba Romana (Folosind AI-ul tau local din Ollama pentru traducere)
    ro_lines = []
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}={n}")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.id=Id")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.version=Versiune")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdBy=Creat de")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdDate=Data crearii")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.lastModifiedBy=Modificat de")
    ro_lines.append(
        f"{COMPANY}.{project_name}.entity/{n}.lastModifiedDate=Data modificarii"
    )
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedBy=Sters de")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedDate=Data stergerii")

    for f_name, _ in fields_list:
        spaced_name = re.sub(r"(?<!^)(?=[A-Z])", " ", f_name).lower()
        # Cerem modelului de 3B sa traduca doar numele campului curent
        prompt = f"Translate the following English technical field name to Romanian. Output ONLY the translated name, capitalized, nothing else. Text: '{spaced_name}'"
        traducere_ro = (
            requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False},
            )
            .json()
            .get("response", "")
            .strip()
        )
        # Plasa de siguranta in caz de lipsa serviciu
        if not traducere_ro or "Error" in traducere_ro:
            traducere_ro = spaced_name.capitalize()
        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={traducere_ro}")

    ro_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}ListView.title=Lista {n}"
    )
    ro_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}DetailView.title=Detalii {n}"
    )

    # 3. Functie interna sigura care scrie in fisier fara sa duplice liniile existente
    def append_unique(file_path, lines_to_add):
        existing_content = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

        with open(file_path, "a", encoding="utf-8") as f:
            # Daca fisierul nu se termina cu newline, adaugam unul ca sa nu lipim prima linie noua de textul vechi
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            for line in lines_to_add:
                key = line.split("=")[0]
                if key not in existing_content:
                    f.write(line + "\n")

    append_unique(en_path, en_lines)
    append_unique(ro_path, ro_lines)
    print(
        "✨ Localizarea in engleza si romana pentru entitatea "
        + n
        + " a fost injectata cu succes!"
    )


def update_menu(n):
    print("Updating menu.xml for " + n + "...")
    menu_path = (
        PROIECT_PATH + f"/src/main/resources/{company_path}/{project_name}/menu.xml"
    )

    if not os.path.exists(menu_path):
        print("⚠️ Nu am gasit fisierul menu.xml la calea specificata!")
        return

    # Generam linia exacta de meniu in formatul Jmix Studio
    menu_item = (
        '    <item view="'
        + n
        + '.list" title="msg://"'
        + COMPANY
        + '"."'
        + project_name
        + '".view.'
        + n.lower()
        + "/"
        + n.lower()
        + 'ListView.title"/>\n'
    )

    with open(menu_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Plasa de siguranta: verificam daca ecranul este deja in meniu
    if ('view="' + n + '.list"') in content:
        print("ℹ️ Ecranul " + n + ".list exista deja in meniu.")
        return

    # Inseram item-ul exact inainte de inchiderea tag-ului principal de meniu
    if "</menu>" in content:
        new_content = content.replace("</menu>", menu_item + "</menu>")
        with open(menu_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Menu injectat cu succes in menu.xml!")
    else:
        print("⚠️ Structura invalida pentru menu.xml (lipsete tag-ul </menu>)!")


def gen_liquibase_changelog(n, fi):
    # 1. Determinăm folderele
    current_year = datetime.now().strftime("%Y")
    current_month = datetime.now().strftime("%m")
    timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")

    target_dir = (
        PROIECT_PATH
        + f"/src/main/resources/{company_path}/{project_name}/liquibase/changelog/{current_year}/{current_month}"
    )
    os.makedirs(target_dir, exist_ok=True)
    filename = f"{target_dir}/{timestamp_id}-{n.lower()}.xml"
    table_name = n.upper()

    def map_type(java_type):
        jt = java_type.lower()
        if jt in ["string"]:
            return "VARCHAR(255)"
        if jt in ["integer"]:
            return "INT"
        if jt in ["long"]:
            return "BIGINT"
        if jt in ["boolean"]:
            return "BOOLEAN"
        if jt in ["localdatetime"]:
            return "timestamp with time zone"
        if jt in ["localdate"]:
            return "DATE"
        if jt in ["uuid"]:
            return "UUID"
        if jt in ["bigdecimal"]:
            return "NUMERIC(19, 2)"
        if jt in ["double"]:
            return "double precision"
        return "VARCHAR(255)"

    # 2. Procesăm lista returnată de get_fields
    fields_list = get_fields(fi)

    xml_columns = ""
    for f_name, f_type in fields_list:
        sql_col_name = f_name.upper()
        sql_type = map_type(f_type)
        xml_columns += (
            f'            <column name="{sql_col_name}" type="{sql_type}" />\n'
        )

    # Structura XML
    xml_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <databaseChangeLog
            xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                          http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd"
            objectQuotingStrategy="QUOTE_ONLY_RESERVED_WORDS">
    <changeSet id="{timestamp_id}-1" author="{PROJECT}">
        <createTable tableName="{table_name}">
            <column name="ID" type="UUID">
                <constraints
					nullable="false"
					primaryKey="true"
					primaryKeyName="PK_{table_name}"
				/>
            </column>
            <column name="VERSION" type="INT">
                <constraints nullable="false" />
            </column>
            <column name="CREATED_BY" type="VARCHAR(255)" />
            <column name="CREATED_DATE" type="timestamp with time zone" />
            <column name="LAST_MODIFIED_BY" type="VARCHAR(255)" />
            <column name="LAST_MODIFIED_DATE" type="timestamp with time zone" />
{xml_columns}        </createTable>
    </changeSet>
</databaseChangeLog>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f" -> Generated Liquibase XML via get_fields(): {filename}")


if __name__ == "__main__":
    if len(sys.argv) > 3:
        a, name, fields = sys.argv[1], sys.argv[2], sys.argv[3]
        if a == "entity":
            gen_entity_mechanic(name, fields)
            update_messages_entity(name, fields)
            gen_liquibase_changelog(name, fields)
        elif a == "ui-list":
            gen_list_ui(name, fields)
            update_menu(name)
        elif a == "ui-detail":
            gen_detail_ui(name, fields)
    else:
        print("Usage: python3 generator.py <entity|ui-list|ui-detail> <name> <fields>")
        exit(1)
