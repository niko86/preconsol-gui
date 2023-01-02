from python_ags4 import AGS4
import pandas as pd

class ProcessAGS:

    def __init__(self, file_name:str) -> None:
        self._file_name = file_name
        self._main()


    def _main(self):
        #self._ags_errors = AGS4.check_file(self._file_name)
        self._ags_tables, self._ags_table_headings = AGS4.AGS4_to_dataframe(self._file_name)
        #if len(errors) == 1 and errors.__contains__('Metadata'):


    def _get_errors(self):
        return self._ags_errors


    def _get_group_headings(self) -> dict:
        return self._ags_table_headings


    def _get_table(self, table_name:str) -> pd.DataFrame:
        return self._ags_tables[table_name]


    def get_cons_for_preconsolidation(self) -> pd.DataFrame | None:
        filter_columns = ['LOCA_ID','SAMP_TOP','SAMP_REF','SAMP_TYPE','SAMP_ID','CONS_INCN','CONS_INCF','CONS_INCE']
        coerse_columns = {'CONS_INCN': 'signed', 'CONS_INCF': 'signed', 'CONS_INCE': 'float'}
        sort_values = ['LOCA_ID', 'SAMP_TOP', 'SAMP_REF', 'CONS_INCN']
        export_columns = ['SAMP_NAME', 'SAMP_ID','CONS_INCN','CONS_INCF','CONS_INCE']

        if 'CONS' in self._ags_table_headings and all(heading in self._ags_table_headings['CONS'] for heading in filter_columns):
            df_cons = self._ags_tables['CONS']
            df_cons = df_cons.filter(filter_columns)
            df_cons = df_cons.drop([0, 1])
            for column, cast_type in coerse_columns.items():
                df_cons[column] = pd.to_numeric(df_cons[column], downcast=cast_type)
            df_cons = df_cons.sort_values(sort_values, ascending=[True, ] * len(sort_values))
            df_cons = df_cons.reset_index(drop=True)
            df_cons['SAMP_NAME'] = df_cons['LOCA_ID'] + '_' + df_cons['SAMP_TOP'] + 'm_' + df_cons['SAMP_TYPE'] + '_' + df_cons['SAMP_REF']
            df_cons = df_cons.filter(export_columns)
            return df_cons
        
        return None


if __name__ == '__main__':
    ags = ProcessAGS('example_4.ags')
    ags.get_cons_for_preconsolidation()
