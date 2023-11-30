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
    <table>
      <thead>
        <tr>
          <th>
            <span className="font-medium">Date & time</span>
          </th>
          <th>
            <span className="font-medium">Location</span>
          </th>
          <th>
            <span className="font-medium">Teams</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {games.map(({ teams, datetime, location }) => (
          <tr key={datetime}>
            <td>
              {format(new Date(datetime), 'Pp', {
                locale,
              })}
            </td>
            <td>{location}</td>
            <td>{teams}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Schedule;
