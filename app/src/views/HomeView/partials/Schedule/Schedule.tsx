import { Table, TableBody, Text } from '@radix-ui/themes';
import { format } from 'date-fns';

const {
  [window.navigator.language.replace('-', '') as keyof typeof import('date-fns/locale')]: locale,
} = await import('date-fns/locale');

interface Game {
  teams: string;
  datetime: string;
  location: string;
}

interface ScheduleProps {
  games: Game[];
}

const Schedule: React.FC<ScheduleProps> = ({ games }) => {
  console.info({ lang: window.navigator.language, locale });

  return (
    <Table.Root variant="surface">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeaderCell>
            <Text weight="medium">Date & time</Text>
          </Table.ColumnHeaderCell>
          <Table.ColumnHeaderCell>
            <Text weight="medium">Location</Text>
          </Table.ColumnHeaderCell>
          <Table.ColumnHeaderCell>
            <Text weight="medium">Teams</Text>
          </Table.ColumnHeaderCell>
        </Table.Row>
      </Table.Header>
      <TableBody>
        {games.map(({ teams, datetime, location }) => (
          <Table.Row key={datetime}>
            <Table.Cell>
              <Text>
                {format(new Date(datetime), 'Pp', {
                  locale,
                })}
              </Text>
            </Table.Cell>
            <Table.Cell>
              <Text>{location}</Text>
            </Table.Cell>
            <Table.Cell>
              <Text>{teams}</Text>
            </Table.Cell>
          </Table.Row>
        ))}
      </TableBody>
    </Table.Root>
  );
};

export default Schedule;
