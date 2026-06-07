#!/usr/bin/env python3
# -
# Copyright (c) 2026 Florin Tanasă <florin.tanasa@gmail.com>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -
#
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# Load proiect path in variable PROIECT_PATH
PROIECT_PATH = str(Path.cwd())


# Function to read the the file settings.gradle file to find and return project name
def get_project_name(settings_path: Path = Path("settings.gradle")) -> str | None:
    text = settings_path.read_text(encoding="utf-8")
    # Find rootProject.name = 'name' or "name"
    m = re.search(r"""rootProject\.name\s*=\s*(['"])(.*?)\1""", text)
    return m.group(2) if m else None  # return only proiect name - like 'onboarding'


# Load in variable PROJECT the name of project
PROJECT = get_project_name()
project_name = (PROJECT or "").lower()  # transform project name in lower letters


# Function to read the the file settings.gradle file to find and return project name
def get_company_name(settings_path: Path = Path("build.gradle")) -> str | None:
    text = settings_path.read_text(encoding="utf-8")
    # Find group = 'com.company' or "com.company"
    m = re.search(r"""group\s*=\s*(['"])(.*?)\1""", text)
    return m.group(2) if m else None  # return only company name - like 'com.company'


# Load in variable COMPANY the name of group
COMPANY = get_company_name() or ""
# Replace char '.' with '/' and transf. in path - like 'com/company'
company_path = COMPANY.replace(".", "/")


# Function to read traits from csv file traits.casv
def get_traits_from_csv(csv_path, target_entity_name):
    """Reading traits.csv file and return global traits of entitties."""
    traits = {
        "versioned": True,
        "audit_of_creation": True,
        "audit_of_modification": True,
        "soft_delete": False,
    }
    # If not is found the traits.csv return traits default: "versioned": True,"audit_of_creation": True, "audit_of_modification": True, "soft_delete": False,
    if not os.path.exists(csv_path):
        return traits

    # Open the traits.csv fiele and return the traits for entity
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["entity_name"].strip().lower() == target_entity_name.lower():
                traits["versioned"] = row["versioned"].strip().lower() == "true"
                traits["audit_of_creation"] = (
                    row["audit_of_creation"].strip().lower() == "true"
                )
                traits["audit_of_modification"] = (
                    row["audit_of_modification"].strip().lower() == "true"
                )
                traits["soft_delete"] = row["soft_delete"].strip().lower() == "true"
                break
    return traits


# Funtion to return global fields of entity
def get_entities_from_csv(csv_path, target_entity_name):
    """Reading entities.csv file and return global fields of entity."""
    fields_list = []
    if not os.path.exists(csv_path):
        print(f" ! Error: The file CSV was not found at : {csv_path}")
        return fields_list

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["entity_name"].strip().lower() == target_entity_name.lower():
                fields_list.append(
                    {
                        "name": row["field_name"].strip(),
                        "type": row["field_type"].strip(),
                        "mandatory": row["mandatory"].strip().lower() == "true",
                        "unique": row["unique"].strip().lower() == "true",
                    }
                )
    return fields_list


# Function to generate java class for an entity with fileds loaded in fields_list, traits and relations from the entities
def gen_entity_mechanic_from_csv(name, fields_list, traits, relations_list=[]):
    table_name = name.upper()  # tranform table name in upper chars

    # Generate unique indexes conform Jmix standard  @Table(indexes=...)
    unique_indexes = []
    for field in fields_list:
        if field["unique"]:
            col_name = field["name"].upper()
            unique_indexes.append(
                f'@Index(name = "IDX_{table_name}_UNQ_{col_name}", columnList = "{col_name}", unique = true)'
            )

    if unique_indexes:
        indexes_str = ",\n        ".join(unique_indexes)
        table_annotation = (
            f'@Table(name = "{table_name}", indexes = {{\n        {indexes_str}\n}})'
        )
    else:
        table_annotation = f'@Table(name = "{table_name}")'

    # Generate the properties, methods, and trait imports in Java
    java_traits_fields = ""
    java_traits_methods = ""
    dinamic_imports = set()

    if traits["versioned"]:
        java_traits_fields += '    @Column(name = "VERSION", nullable = false)\n    @Version\n    private Integer version;\n\n'
        java_traits_methods += "    public Integer getVersion() {\n        return version;\n    }\n\n    public void setVersion(Integer version) {\n        this.version = version;\n    }\n\n"

    if traits["audit_of_creation"]:
        java_traits_fields += '    @CreatedBy\n    @Column(name = "CREATED_BY")\n    private String createdBy;\n\n    @CreatedDate\n    @Column(name = "CREATED_DATE")\n    private OffsetDateTime createdDate;\n\n'
        java_traits_methods += "    public String getCreatedBy() {\n        return createdBy;\n    }\n\n    public void setCreatedBy(String createdBy) {\n        this.createdBy = createdBy;\n    }\n\n"
        java_traits_methods += "    public OffsetDateTime getCreatedDate() {\n        return createdDate;\n    }\n\n    public void setCreatedDate(OffsetDateTime createdDate) {\n        this.createdDate = createdDate;\n    }\n\n"
        dinamic_imports.add("import org.springframework.data.annotation.CreatedBy;")
        dinamic_imports.add("import org.springframework.data.annotation.CreatedDate;")
        dinamic_imports.add("import java.time.OffsetDateTime;")

    if traits["audit_of_modification"]:
        java_traits_fields += '    @LastModifiedBy\n    @Column(name = "LAST_MODIFIED_BY")\n    private String lastModifiedBy;\n\n    @LastModifiedDate\n    @Column(name = "LAST_MODIFIED_DATE")\n    private OffsetDateTime lastModifiedDate;\n\n'
        java_traits_methods += "    public String getLastModifiedBy() {\n        return lastModifiedBy;\n    }\n\n    public void setLastModifiedBy(String lastModifiedBy) {\n        this.lastModifiedBy = lastModifiedBy;\n    }\n\n"
        java_traits_methods += "    public OffsetDateTime getLastModifiedDate() {\n        return lastModifiedDate;\n    }\n\n    public void setLastModifiedDate(OffsetDateTime lastModifiedDate) {\n        this.lastModifiedDate = lastModifiedDate;\n    }\n\n"
        dinamic_imports.add(
            "import org.springframework.data.annotation.LastModifiedBy;"
        )
        dinamic_imports.add(
            "import org.springframework.data.annotation.LastModifiedDate;"
        )
        dinamic_imports.add("import java.time.OffsetDateTime;")

    if traits["soft_delete"]:
        java_traits_fields += '    @DeletedBy\n    @Column(name = "DELETED_BY")\n    private String deletedBy;\n\n    @DeletedDate\n    @Column(name = "DELETED_DATE")\n    private OffsetDateTime deletedDate;\n\n'
        java_traits_methods += "    public String getDeletedBy() {\n        return deletedBy;\n    }\n\n    public void setDeletedBy(String deletedBy) {\n        this.deletedBy = deletedBy;\n    }\n\n"
        java_traits_methods += "    public OffsetDateTime getDeletedDate() {\n        return deletedDate;\n    }\n\n    public void setDeletedDate(OffsetDateTime deletedDate) {\n        this.deletedDate = deletedDate;\n    }\n\n"
        dinamic_imports.add("import io.jmix.core.annotation.DeletedBy;")
        dinamic_imports.add("import io.jmix.core.annotation.DeletedDate;")

    # Generăm câmpurile de business și colectăm importurile necesare
    java_business_fields = ""
    java_business_methods = ""
    is_first_text = True

    for field in fields_list:
        f_name = field["name"]
        f_type = field["type"]
        sql_col_name = f_name.upper()

        # Colectăm tipurile în setul global unic
        if f_type == "BigDecimal":
            dinamic_imports.add("import java.math.BigDecimal;")
        elif f_type == "LocalDate":
            dinamic_imports.add("import java.time.LocalDate;")
        elif f_type == "LocalDateTime":
            dinamic_imports.add("import java.time.LocalDateTime;")

        column_props = f'name = "{sql_col_name}"'
        if field["mandatory"]:
            column_props += ", nullable = false"

        instance_name_annotation = ""
        if f_type.lower() == "string" and is_first_text:
            instance_name_annotation = "    @InstanceName\n"
            is_first_text = False

        java_business_fields += f"{instance_name_annotation}    @Column({column_props})\n    private {f_type} {f_name};\n\n"

        f_caps = f_name[0].upper() + f_name[1:]
        java_business_methods += f"    public {f_type} get{f_caps}() {{\n        return {f_name};\n    }}\n\n    public void set{f_caps}({f_type} {f_name}) {{\n        this.{f_name} = {f_name};\n    }}\n\n"

    # Generate fields and methods for relationships
    java_relation_fields = ""
    java_relation_methods = ""

    for rel in relations_list:
        # For the ManyToOne (N:1) relationship case
        if rel["type"] == "N:1":
            f_name = rel["field"]
            tgt_class = rel["target"]
            sql_fk_col = f"{f_name.upper()}_ID"

            # Add imports to the unique global set
            dinamic_imports.add("import jakarta.persistence.FetchType;")
            dinamic_imports.add("import jakarta.persistence.ManyToOne;")
            dinamic_imports.add("import jakarta.persistence.JoinColumn;")

            join_props = f'name = "{sql_fk_col}"'
            if rel["mandatory"]:
                join_props += ", nullable = false"

            java_relation_fields += f"    @JoinColumn({join_props})\n"
            java_relation_fields += "    @ManyToOne(fetch = FetchType.LAZY)\n"
            java_relation_fields += f"    private {tgt_class} {f_name};\n\n"

            f_caps = f_name[0].upper() + f_name[1:]
            java_relation_methods += f"    public {tgt_class} get{f_caps}() {{\n        return {f_name};\n    }}\n\n"
            java_relation_methods += f"    public void set{f_caps}({tgt_class} {f_name}) {{\n        this.{f_name} = {f_name};\n    }}\n\n"

        # For the OneToMany (1:N) relationship case
        elif rel["type"] == "1:N":
            f_name = rel["field"]  # ex: steps
            tgt_class = rel["target"]  # ex: UserStep

            # Automatically determine the mappedBy field name from the target entity.
            # Jmix uses the lowercase version of the source class name.
            # If the source class has an underscore (User_), we remove it to comply with the Java convention.
            mapped_by_field = name[0].lower() + name[1:]
            if mapped_by_field.endswith("_"):
                mapped_by_field = mapped_by_field[:-1]  # ex: becomes "user"

            # Add the necessary imports to the dynamic global set
            dinamic_imports.add("import jakarta.persistence.OneToMany;")
            dinamic_imports.add("import java.util.List;")

            # 1. List<UserStep> property
            java_relation_fields += f'    @OneToMany(mappedBy = "{mapped_by_field}")\n'
            java_relation_fields += f"    private List<{tgt_class}> {f_name};\n\n"

            # 2. Getter and Setter methods specific for the collection
            f_caps = f_name[0].upper() + f_name[1:]
            java_relation_methods += f"    public List<{tgt_class}> get{f_caps}() {{\n        return {f_name};\n    }}\n\n"
            java_relation_methods += f"    public void set{f_caps}(List<{tgt_class}> {f_name}) {{\n        this.{f_name} = {f_name};\n    }}\n\n"

        # For the OneToOne (1:1) relationship case
        elif rel["type"] == "1:1":
            f_name = rel["field"]
            tgt_class = rel["target"]
            sql_fk_col = f"{f_name.upper()}_ID"

            dinamic_imports.add("import jakarta.persistence.OneToOne;")
            dinamic_imports.add("import jakarta.persistence.FetchType;")
            dinamic_imports.add("import jakarta.persistence.JoinColumn;")

            join_props = f'name = "{sql_fk_col}"'
            if rel["mandatory"]:
                join_props += ", nullable = false"

            java_relation_fields += f"    @JoinColumn({join_props})\n"
            java_relation_fields += "    @OneToOne(fetch = FetchType.LAZY)\n"
            java_relation_fields += f"    private {tgt_class} {f_name};\n\n"

            f_caps = f_name[0].upper() + f_name[1:]
            java_relation_methods += f"    public {tgt_class} get{f_caps}() {{\n        return {f_name};\n    }}\n\n"
            java_relation_methods += f"    public void set{f_caps}({tgt_class} {f_name}) {{\n        this.{f_name} = {f_name};\n    }}\n\n"

        # For the ManyToMany (N:N) relationship case
        elif rel["type"] == "N:N":
            f_name = rel["field"]
            tgt_class = rel["target"]
            join_table_name = (
                f"{name.upper()}_{tgt_class.upper()}_LINK"  # ex: USER__ROLE_LINK
            )

            src_fk_col = f"{name.upper()}_ID"
            tgt_fk_col = f"{tgt_class.upper()}_ID"

            dinamic_imports.add("import jakarta.persistence.ManyToMany;")
            dinamic_imports.add("import jakarta.persistence.JoinTable;")
            dinamic_imports.add("import jakarta.persistence.JoinColumn;")
            dinamic_imports.add("import java.util.List;")

            java_relation_fields += "    @ManyToMany\n"
            java_relation_fields += f'    @JoinTable(name = "{join_table_name}",\n'
            java_relation_fields += (
                f'            joinColumns = @JoinColumn(name = "{src_fk_col}"),\n'
            )
            java_relation_fields += f'            inverseJoinColumns = @JoinColumn(name = "{tgt_fk_col}"))\n'
            java_relation_fields += f"    private List<{tgt_class}> {f_name};\n\n"

            f_caps = f_name[0].upper() + f_name[1:]
            java_relation_methods += f"    public List<{tgt_class}> get{f_caps}() {{\n        return {f_name};\n    }}\n\n"
            java_relation_methods += f"    public void set{f_caps}(List<{tgt_class}> {f_name}) {{\n        this.{f_name} = {f_name};\n    }}\n\n"

    # Transform the entire import set into text NOW, after everything is collected
    imports_block = "\n".join(sorted(list(dinamic_imports)))
    if imports_block:
        imports_block += "\n"

    # ======== Final Java class structure ========
    java_content = f"""package {COMPANY}.{project_name}.entity;

import io.jmix.core.entity.annotation.JmixGeneratedValue;
import io.jmix.core.metamodel.annotation.InstanceName;
import io.jmix.core.metamodel.annotation.JmixEntity;
import jakarta.persistence.*;
import java.util.UUID;
{imports_block}
@JmixEntity
{table_annotation}
@Entity
public class {name} {{

    @Id
    @Column(name = "ID", nullable = false)
    @JmixGeneratedValue
    private UUID id;

{java_traits_fields}{java_business_fields}{java_relation_fields}    public UUID getId() {{
        return id;
    }}

    public void setId(UUID id) {{
        this.id = id;
    }}

{java_traits_methods}{java_business_methods}{java_relation_methods}}}
"""

    # Write the file directly into the correct project structure
    td = PROIECT_PATH + f"/src/main/java/{company_path}/{project_name}/entity"
    if not os.path.exists(td):
        os.makedirs(td)

    java_path = td + "/" + name + ".java"
    open(java_path, "w", encoding="utf-8").write(java_content)
    print("✨ Entity mecanic salvat cu succes in: " + java_path)


def gen_liquibase_changelog_from_csv(name, fields_list, traits):
    timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
    table_name = name.upper()

    # 1. Map CSV data types to SQL data types recognized by Liquibase
    def map_type(java_type):
        jt = java_type.lower()
        if jt in ["string", "text"]:
            return "VARCHAR(255)"
        if jt in ["integer", "int"]:
            return "INT"
        if jt in ["long"]:
            return "BIGINT"
        if jt in ["boolean", "bool"]:
            return "BOOLEAN"
        if jt in ["date", "localdate"]:
            return "date"
        if jt in ["datetime", "localdatetime", "offsetdatetime"]:
            return "timestamp with time zone"
        if jt in ["uuid"]:
            return "UUID"
        if jt in ["double"]:
            return "double precision"
        if jt in ["bigdecimal"]:
            return "NUMERIC(19, 2)"
        return "VARCHAR(255)"

    # 2. Generate infrastructure columns (Traits) based on traits.csv
    xml_traits_columns = '            <column name="ID" type="UUID">\n'
    xml_traits_columns += f'                <constraints nullable="false" primaryKey="true" primaryKeyName="PK_{table_name}"/>\n'
    xml_traits_columns += "            </column>\n"

    if traits["versioned"]:
        xml_traits_columns += '            <column name="VERSION" type="INT">\n                <constraints nullable="false" />\n            </column>\n'
    if traits["audit_of_creation"]:
        xml_traits_columns += (
            '            <column name="CREATED_BY" type="VARCHAR(255)" />\n'
        )
        xml_traits_columns += '            <column name="CREATED_DATE" type="timestamp with time zone" />\n'
    if traits["audit_of_modification"]:
        xml_traits_columns += (
            '            <column name="LAST_MODIFIED_BY" type="VARCHAR(255)" />\n'
        )
        xml_traits_columns += '            <column name="LAST_MODIFIED_DATE" type="timestamp with time zone" />\n'
    if traits["soft_delete"]:
        xml_traits_columns += (
            '            <column name="DELETED_BY" type="VARCHAR(255)" />\n'
        )
        xml_traits_columns += '            <column name="DELETED_DATE" type="timestamp with time zone" />\n'

    # 3. Generate business columns and collect unique index structure
    xml_business_columns = ""
    xml_indexes = ""

    for field in fields_list:
        sql_col_name = field["name"].upper()
        sql_type = map_type(field["type"])

        # Constrângeri la nivel de coloană (ex: nullable)
        constraints = ""
        if field["mandatory"]:
            constraints = '                <constraints nullable="false" />\n'

        if constraints:
            xml_business_columns += f'            <column name="{sql_col_name}" type="{sql_type}">\n{constraints}            </column>\n'
        else:
            xml_business_columns += (
                f'            <column name="{sql_col_name}" type="{sql_type}" />\n'
            )

        # If the field in CSV is marked as UNIQUE, generate a separate <createIndex> element
        # (Just like EclipseLink generates separately based on @Index)
        if field["unique"]:
            index_name = f"IDX_{table_name}_UNQ_{sql_col_name}"
            xml_indexes += f"""
    <changeSet id="{timestamp_id}-idx-{field["name"].lower()}" author="{project_name}">
        <createIndex tableName="{table_name}" indexName="{index_name}" unique="true">
            <column name="{sql_col_name}"/>
        </createIndex>
    </changeSet>"""

    # 4. Assemble the XML structure with Jmix/Liquibase official namespaces
    xml_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<databaseChangeLog
	xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd"
	objectQuotingStrategy="QUOTE_ONLY_RESERVED_WORDS"
>
    <changeSet id="{timestamp_id}-1" author="{project_name}">
        <createTable tableName="{table_name}">
{xml_traits_columns}{xml_business_columns}        </createTable>
    </changeSet>{xml_indexes}
</databaseChangeLog>
"""

    # 5. Save the file on disk in a chronological subfolder structure
    current_year = datetime.now().strftime("%Y")
    current_month = datetime.now().strftime("%m")
    target_dir = (
        PROIECT_PATH
        + f"/src/main/resources/com/company/onboarding/liquibase/changelog/{current_year}/{current_month}"
    )
    os.makedirs(target_dir, exist_ok=True)

    filename = f"{target_dir}/{timestamp_id}-01_base-{name.lower()}.xml"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f" -> Generated Liquibase XML with Constraints & Indexes: {filename}")


def get_relations_from_csv(csv_path, target_entity_name):
    """Citește relations.csv și returnează doar relațiile unde entitatea curentă este sursa."""
    relations_list = []
    if not os.path.exists(csv_path):
        return relations_list

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["source_entity"].strip().lower() == target_entity_name.lower():
                relations_list.append(
                    {
                        "type": row["relation_type"].strip(),
                        "target": row["target_entity"].strip(),
                        "field": row["field_name"].strip(),
                        "mandatory": row["mandatory"].strip().lower() == "true",
                    }
                )
    return relations_list


# Function to generate Liquibase relationships
def gen_liquibase_relations_changelog(name, relations_list):
    if not relations_list:
        return

    timestamp_id = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )  # Generate a timestamp string in YYYYMMDDHHMMSS format
    src_table = name.upper()  # Convert the input 'name' to uppercase

    xml_fk_content = (
        ""  # Initialize an empty string to store the XML content for foreign keys
    )
    for rel in relations_list:  # Iterate through the list of relationships
        tgt_table = rel["target"].upper()  # Convert the target table name to uppercase
        # EXCEPTION FOR JMIX: If the target is the "USER" class, the actual SQL table is USER_
        if tgt_table == "USER":
            tgt_table = "USER_"  # Adjust the table name to "USER_"
        # === CASE 1: N:1 Relationship (ManyToOne) ===
        if rel["type"] == "N:1":  # If the relationship type is N:1
            f_name = rel["field"].upper()
            col_name = f"{f_name}_ID"
            fk_name = f"FK_{src_table}_ON_{f_name}"
            nullable_val = (
                "false" if rel["mandatory"] else "true"
            )  # Set the nullable value based on whether the field is mandatory

            xml_fk_content += f"""
    <changeSet id="{timestamp_id}-add-fk-{rel["field"].lower()}" author="{project_name}">
        <addColumn tableName="{src_table}">
            <column name="{col_name}" type="UUID">
                <constraints nullable="{nullable_val}"/>
            </column>
        </addColumn>
        <addForeignKeyConstraint baseTableName="{src_table}"
                                  baseColumnNames="{col_name}"
                                  constraintName="{fk_name}"
                                  referencedTableName="{tgt_table}"
                                  referencedColumnNames="ID"/>
    </changeSet>"""

        # === CASE 2: 1:1 Relationship (OneToOne) ===
        # Add a UUID column + Foreign Key + a UNIQUE constraint to ensure the 1-to-1 link
        elif rel["type"] == "1:1":
            f_name = rel["field"].upper()
            col_name = f"{f_name}_ID"
            fk_name = f"FK_{src_table}_ON_{f_name}"
            nullable_val = "false" if rel["mandatory"] else "true"

            xml_fk_content += f"""
    <changeSet id="{timestamp_id}-add-11-{rel["field"].lower()}" author="{project_name}">
        <addColumn tableName="{src_table}">
            <column name="{col_name}" type="UUID">
                <constraints nullable="{nullable_val}"/>
            </column>
        </addColumn>
        <!-- Garantăm unicitatea la nivel SQL pentru 1:1 prin crearea unui Index UNIQUE -->
        <createIndex tableName="{src_table}" indexName="IDX_{src_table}_UNQ_{col_name}" unique="true">
            <column name="{col_name}"/>
        </createIndex>
        <addForeignKeyConstraint baseTableName="{src_table}"
                                  baseColumnNames="{col_name}"
                                  constraintName="{fk_name}"
                                  referencedTableName="{tgt_table}"
                                  referencedColumnNames="ID"/>
    </changeSet>"""

        # === CASE 3: N:N Relationship (ManyToMany) ===
        # DO NOT add columns in existing tables, but create a completely new linking table
        elif rel["type"] == "N:N":
            join_table = f"{src_table}_{tgt_table}_LINK"
            src_fk = f"{src_table}_ID"
            tgt_fk = f"{tgt_table}_ID"

            xml_fk_content += f"""
    <changeSet id="{timestamp_id}-create-nn-{join_table.lower()}" author="{project_name}">
        <createTable tableName="{join_table}">
            <column name="{src_fk}" type="UUID">
                <constraints nullable="false"/>
            </column>
            <column name="{tgt_fk}" type="UUID">
                <constraints nullable="false"/>
            </column>
        </createTable>
        <addPrimaryKey tableName="{join_table}" columnNames="{src_fk}, {tgt_fk}" constraintName="PK_{join_table}"/>
        <addForeignKeyConstraint baseTableName="{join_table}" baseColumnNames="{src_fk}"
                                  constraintName="FK_{join_table}_ON_{src_table}"
                                  referencedTableName="{src_table}" referencedColumnNames="ID"/>
        <addForeignKeyConstraint baseTableName="{join_table}" baseColumnNames="{tgt_fk}"
                                  constraintName="FK_{join_table}_ON_{tgt_table}"
                                  referencedTableName="{tgt_table}" referencedColumnNames="ID"/>
    </changeSet>"""

    if not xml_fk_content:
        return

    xml_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<databaseChangeLog
	xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                      http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd"
	objectQuotingStrategy="QUOTE_ONLY_RESERVED_WORDS"
>
{xml_fk_content}
</databaseChangeLog>
"""

    current_year = datetime.now().strftime("%Y")
    current_month = datetime.now().strftime("%m")
    target_dir = (
        PROIECT_PATH
        + f"/src/main/resources/com/company/onboarding/liquibase/changelog/{current_year}/{current_month}"
    )
    os.makedirs(target_dir, exist_ok=True)

    filename = f"{target_dir}/{timestamp_id}_02_relations_{name.lower()}.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f" -> Generated Liquibase Relations XML: {filename}")


# Function to generate the list-view screen
def gen_list_view_from_csv(name, fields_list, relations_list=[]):
    lower_name = name.lower()  # Convert the input 'name' to lowercase

    # 1. Generăm coloanele simple din entities.csv
    xml_columns = ""
    for field in fields_list:
        f_name = field["name"]  # Get the field name from the 'fields_list'
        xml_columns += f'            <column property="{f_name}"/>\n'  # Add a <column> element with the field name as the property

    # 2. Dynamically generate the Fetch Plan and columns for relationships
    xml_fetch_plan_properties = (
        ""  # Initialize an empty string to store the Fetch Plan block.
    )
    for rel in relations_list:
        if rel["type"] == "N:1":
            f_name = rel["field"]  # ex: step, user

            # Tell the Fetch Plan to load the relationship property with its basic attributes (_base)
            xml_fetch_plan_properties += (
                f'                <property name="{f_name}" fetchPlan="_base"/>\n'
            )

            # Add the column to the table using the dot notation (property.instanceNameField)
            # In Jmix, if is directly set property="step", it will automatically call the field marked with @InstanceName from that entity!
            xml_columns += f'            <column property="{f_name}"/>\n'

    # Construct the Fetch Plan block only if relationships are defined
    xml_fetch_plan_block = ""
    # Check if the xml_fetch_plan_properties dictionary is not empty.
    if xml_fetch_plan_properties:
        xml_fetch_plan_block = f"""            <fetchPlan extends="_base">
{xml_fetch_plan_properties}            </fetchPlan>"""

    # 3. XML FlowUI Structure for a Fully Functional List
    xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<view xmlns="http://jmix.io/schema/flowui/view"
	  xmlns:c="http://jmix.io/schema/flowui/jpql-condition"
      title="msg://{lower_name}ListView.title"
      focusComponent="{lower_name}sDataGrid">
    <data readOnly="true">
        <collection id="{lower_name}sDc" class="{COMPANY}.{project_name}.entity.{name}">
{xml_fetch_plan_block}
            <loader id="{lower_name}sDl" readOnly="true">
                <query>
                	<![CDATA[select e from {name} e]]>
                </query>
            </loader>
        </collection>
    </data>
    <facets>
        <dataLoadCoordinator auto="true"/>
    </facets>
    <layout>
        <hbox id="buttonsPanel" classNames="buttons-panel">
            <button id="createBtn" action="{lower_name}sDataGrid.create"/>
            <button id="editBtn" action="{lower_name}sDataGrid.edit"/>
            <button id="removeBtn" action="{lower_name}sDataGrid.remove"/>
        </hbox>
        <dataGrid id="{lower_name}sDataGrid" width="100%" minHeight="20em" dataContainer="{lower_name}sDc">
            <actions>
                <action id="create" type="list_create"/>
                <action id="edit" type="list_edit"/>
                <action id="remove" type="list_remove"/>
            </actions>
            <columns>
{xml_columns}            </columns>
        </dataGrid>
    </layout>
</view>
"""

    # 4. Java Controller Structure for the list-view
    java_content = f"""package {COMPANY}.{project_name}.view.{lower_name};

import {COMPANY}.{project_name}.entity.{name};
import {COMPANY}.{project_name}.view.main.MainView;
import com.vaadin.flow.router.Route;
import io.jmix.flowui.view.*;

@Route(value = "{lower_name}s", layout = MainView.class)
@ViewController("{name}.list")
@ViewDescriptor("{lower_name}-list-view.xml")
@LookupComponent("{lower_name}sDataGrid")
@DialogMode(width = "64em", height = "48em")
public class {name}ListView extends StandardListView<{name}> {{
}}
"""

    # Writing to Disk
    view_dir = f"{PROIECT_PATH}/src/main/resources/com/company/{project_name}/view/{lower_name}"
    java_dir = (
        f"{PROIECT_PATH}/src/main/java/com/company/{project_name}/view/{lower_name}"
    )
    os.makedirs(view_dir, exist_ok=True)
    os.makedirs(java_dir, exist_ok=True)

    with open(f"{view_dir}/{lower_name}-list-view.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    with open(f"{java_dir}/{name}ListView.java", "w", encoding="utf-8") as f:
        f.write(java_content)
    print(f" 🖥️ Successfully generated List View for: {name}")


# Function to generate the detail-view screen
def gen_detail_view_from_csv(name, fields_list, relations_list=[]):
    lower_name = name.lower()

    # 1. Generate the form components dynamically
    xml_form_components = ""
    for field in fields_list:
        f_name = field["name"]
        f_type = field["type"].lower()

        if f_type in ["boolean", "bool"]:
            xml_form_components += (
                f'            <checkbox id="{f_name}Field" property="{f_name}"/>\n'
            )
        elif f_type in ["date", "localdate", "datetime", "localdatetime"]:
            xml_form_components += (
                f'            <datePicker id="{f_name}Field" property="{f_name}"/>\n'
            )
        else:
            xml_form_components += (
                f'            <textField id="{f_name}Field" property="{f_name}"/>\n'
            )

    # 2. Add the intelligent entityComboBox component for N:1 relationships
    xml_relation_data_containers = ""
    for rel in relations_list:
        if rel["type"] == "N:1":
            f_name = rel["field"]  # ex: step, user
            tgt_class = rel["target"]  # ex: Step, User_
            tgt_lower = tgt_class.lower()

            # Build a dynamic CollectionContainer to load data from the target table
            xml_relation_data_containers += f'        <collection id="{tgt_lower}sDc" class="{COMPANY}.{project_name}.entity.{tgt_class}">\n'
            xml_relation_data_containers += '            <fetchPlan extends="_base"/>\n'
            xml_relation_data_containers += (
                f'            <loader id="{tgt_lower}sDl">\n'
            )
            xml_relation_data_containers += "                <query>"
            xml_relation_data_containers += (
                f"                   <![CDATA[select e from {tgt_class} e]]>"
            )
            xml_relation_data_containers += "                </query>\n"
            xml_relation_data_containers += "            </loader>\n"
            xml_relation_data_containers += "        </collection>\n"

            # Add the entityCombobox component connected to the itemsContainer
            xml_form_components += f'            <entityComboBox id="{f_name}Field" property="{f_name}" itemsContainer="{tgt_lower}sDc"/>\n'

    # 2. XML FlowUI Structure for detail-view
    xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<view xmlns="http://jmix.io/schema/flowui/view"
      title="msg://{lower_name}DetailView.title"
      focusComponent="form">
    <data>
    	<instance id="{lower_name}Dc"
                  class="{COMPANY}.{project_name}.entity.{name}">
            <fetchPlan extends="_base"/>
            <loader id="{lower_name}Dl"/>
        </instance>
{xml_relation_data_containers}    </data>
    <facets>
        <dataLoadCoordinator auto="true"/>
    </facets>
    <actions>
        <action id="saveAction" type="detail_saveClose"/>
        <action id="closeAction" type="detail_close"/>
    </actions>
    <layout classNames="fluid-layout" width="100%">
        <formLayout id="form" dataContainer="{lower_name}Dc">
{xml_form_components}        </formLayout>
        <hbox id="detailActions">
            <button id="saveAndCloseBtn" action="saveAction"/>
            <button id="closeBtn" action="closeAction"/>
        </hbox>
    </layout>
</view>
"""

    # 3. Java Controller Structure for detail-view
    java_content = f"""package {COMPANY}.{project_name}.view.{lower_name};

import {COMPANY}.{project_name}.entity.{name};
import {COMPANY}.{project_name}.view.main.MainView;
import com.vaadin.flow.router.Route;
import io.jmix.flowui.view.*;

@Route(value = "{lower_name}s/:id", layout = MainView.class)
@ViewController("{name}.detail")
@ViewDescriptor("{lower_name}-detail-view.xml")
@EditedEntityContainer("{lower_name}Dc")
public class {name}DetailView extends StandardDetailView<{name}> {{
}}
"""

    view_dir = f"{PROIECT_PATH}/src/main/resources/com/company/{project_name}/view/{lower_name}"
    java_dir = (
        f"{PROIECT_PATH}/src/main/java/com/company/{project_name}/view/{lower_name}"
    )
    os.makedirs(view_dir, exist_ok=True)
    os.makedirs(java_dir, exist_ok=True)

    with open(f"{view_dir}/{lower_name}-detail-view.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    with open(f"{java_dir}/{name}DetailView.java", "w", encoding="utf-8") as f:
        f.write(java_content)
    print(f" 🖥️ Detail View successfully generated for: {name}")


# Function to generate messagges in English and to tranlsate in Romanian using Ollama with model translategemma:4b
def update_messages_entity(n, fields_list, traits, relations_list=[]):
    print("Generating localization messages for " + n + "...")

    base_path = PROIECT_PATH + f"/src/main/resources/{company_path}/{project_name}"
    en_path = base_path + "/messages_en.properties"
    ro_path = base_path + "/messages_ro.properties"

    en_lines = []
    ro_lines = []

    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}={n}")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}={n}")
    en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.id=Id")
    ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.id=Id")

    if traits["versioned"]:
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.version=Version")
        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.version=Versiune")
    if traits["audit_of_creation"]:
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdBy=Created by")
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdDate=Created date")
        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdBy=Creat de")
        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.createdDate=Data creării")
    if traits["audit_of_modification"]:
        en_lines.append(
            f"{COMPANY}.{project_name}.entity/{n}.lastModifiedBy=Last modified by"
        )
        en_lines.append(
            f"{COMPANY}.{project_name}.entity/{n}.lastModifiedDate=Last modified date"
        )
        ro_lines.append(
            f"{COMPANY}.{project_name}.entity/{n}.lastModifiedBy=Modificat de"
        )
        ro_lines.append(
            f"{COMPANY}.{project_name}.entity/{n}.lastModifiedDate=Data modificării"
        )
    if traits["soft_delete"]:
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedBy=Deleted by")
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedDate=Deleted date")
        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.deletedBy=Șters de")
        ro_lines.append(
            f"{COMPANY}.{project_name}.entity/{n}.deletedDate=Data ștergerii"
        )

    # 1. GENERATE AND TRANSLATE BUSINESS FIELDS (entities.csv)
    for field in fields_list:
        f_name = field["name"]

        # Separate camelCase with spaces (e.g., dueDate -> due date)
        spaced_name = (
            "".join([" " + c if c.isupper() else c for c in f_name]).strip().lower()
        )

        # readable_en is constructed from spaced_name, with only the first letter capitalized!
        readable_en = spaced_name.capitalize()
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={readable_en}")

        prompt = f"Translate this English field name to Romanian. Return ONLY the translated text capitalized. Source: {readable_en}"
        try:
            traducere_ro = (
                requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "translategemma:4b",
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=5,
                )
                .json()
                .get("response", "")
                .strip()
            )
        except Exception:
            traducere_ro = ""

        lungime_text = len(traducere_ro)
        if not traducere_ro or "Error" in traducere_ro or lungime_text > 50:
            traducere_ro = readable_en

        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={traducere_ro}")

    # 2. GENERATE AND TRANSLATE RELATIONSHIP LABELS (relations.csv)
    for rel in relations_list:
        f_name = rel["field"]

        # Separate camelCase with spaces for relationships
        spaced_name = (
            "".join([" " + c if c.isupper() else c for c in f_name]).strip().lower()
        )
        readable_en = spaced_name.capitalize()
        en_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={readable_en}")

        prompt = f"Translate this English field name to Romanian. Return ONLY the translated text capitalized. Source: {readable_en}"
        try:
            traducere_ro = (
                requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "translategemma:4b",
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=5,
                )
                .json()
                .get("response", "")
                .strip()
            )
        except Exception:
            traducere_ro = ""

        lungime_text = len(traducere_ro)
        if not traducere_ro or "Error" in traducere_ro or lungime_text > 50:
            traducere_ro = readable_en

        ro_lines.append(f"{COMPANY}.{project_name}.entity/{n}.{f_name}={traducere_ro}")

    # 3. TITLES FOR VISUAL UI SCREENS GENERATED
    en_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}ListView.title={n}s"
    )
    en_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}DetailView.title={n} detail"
    )

    ro_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}ListView.title=Lista {n}"
    )
    ro_lines.append(
        f"{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}DetailView.title=Detalii {n}"
    )

    # 4. The internal function that adds unique lines
    def append_unique(file_path, lines_to_add):
        existing_content = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

        with open(file_path, "a", encoding="utf-8") as f:
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            for line in lines_to_add:
                key = line.split("=")[0]
                if key not in existing_content:
                    f.write(line + "\n")

    append_unique(en_path, en_lines)
    append_unique(ro_path, ro_lines)
    print(
        "✨ Localization in English and Romanian for the entity "
        + n
        + " successfully injected!"
    )


# Function for update the menu
def update_menu(n):
    print("Updating menu.xml for " + n + "...")
    menu_path = (
        PROIECT_PATH + f"/src/main/resources/{company_path}/{project_name}/menu.xml"
    )

    # Check and inform if not exist the menu.xml file in the path
    if not os.path.exists(menu_path):
        print(f"⚠️ I not found the file menu.xml in the path {menu_path}!")
        return

    # Generate the exact menu line in the Jmix Studio format
    menu_item = f'    <item view="{n}.list" title="msg://{COMPANY}.{project_name}.view.{n.lower()}/{n.lower()}ListView.title"/>\n'

    with open(menu_path, "r", encoding="utf-8") as f:
        content = f.read()

    # For safety: check if the screen is already in the menu
    if ('view="' + n + '.list"') in content:
        print("ℹ️ View " + n + ".list allready exist in menu.")
        return

    # Insert the exact item right before the closing tag of the main menu
    if "</menu>" in content:
        new_content = content.replace("</menu>", menu_item + "</menu>")
        with open(menu_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Menu injected successfully into menu.xml!")
    else:
        print("⚠️ Invalid structure for menu.xml (missing closing </menu> tag)!")


if __name__ == "__main__":
    # Verify the correct number of arguments (script + action + entity name)
    if len(sys.argv) < 3:
        print("Usage: python3 jmix-cli.py [entity|ui-list|ui-detail] [Name]")
        sys.exit(1)

    action = sys.argv[1]  # Ex: entity
    name = sys.argv[2]  # Ex: Department

    if action == "entity":
        # Fetch data from the normalized files in the CSV files
        traits = get_traits_from_csv("traits.csv", name)
        fields_list = get_entities_from_csv("entities.csv", name)
        relations_list = get_relations_from_csv("relations.csv", name)

        if not fields_list:
            print(f" ⚠ No fields found for the entity '{name}' in entities.csv")
            sys.exit(1)

        print(f"Generating Entity {name} from CSV architecture...")
        gen_entity_mechanic_from_csv(name, fields_list, traits, relations_list)
        update_messages_entity(name, fields_list, traits, relations_list)
        gen_liquibase_changelog_from_csv(name, fields_list, traits)
        if relations_list:
            gen_liquibase_relations_changelog(name, relations_list)

    elif action == "ui-list":
        fields_list = get_entities_from_csv("entities.csv", name)
        relations_list = get_relations_from_csv("relations.csv", name)
        if not fields_list:
            print(f" ⚠ Error: Fields for entity '{name}' do not exist in entities.csv")
            sys.exit(1)
        gen_list_view_from_csv(name, fields_list, relations_list)
        update_menu(name)

    elif action == "ui-detail":
        fields_list = get_entities_from_csv("entities.csv", name)
        relations_list = get_relations_from_csv("relations.csv", name)
        if not fields_list:
            print(f" ⚠ Error: Fields for '{name}' do not exist in entities.csv")
            sys.exit(1)
        gen_detail_view_from_csv(name, fields_list, relations_list)

    else:
        print(f" ⚠ Unknown action: '{action}'. Use entity, ui-list or ui-detail.")
        sys.exit(1)
